# API Response Data Exposure Review

## Overview

This document reviews API response schemas for potential sensitive data exposure and provides recommendations for minimizing data exposure in the ZimAgriTrust platform.

## Findings

### Critical Issues

#### 1. National ID Exposure in UserResponse
**File:** `backend/app/schemas/auth.py`
**Issue:** The `UserResponse` schema includes `national_id: Optional[str] = None` which exposes sensitive PII.

**Current Code:**
```python
class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    masked_phone: str
    role: UserRole
    trust_score: int
    id_verified: bool
    national_id: Optional[str] = None  # ❌ Sensitive PII exposed
    email: Optional[str] = None
    # ... other fields
```

**Recommendation:** Remove `national_id` from the public `UserResponse` schema. This field should only be accessible to:
- Admin users with appropriate permissions
- The user themselves (via a dedicated profile endpoint)
- Verification services (internal use only)

**Fix:**
```python
class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    masked_phone: str
    role: UserRole
    trust_score: int
    id_verified: bool
    # national_id removed from public response
    email: Optional[str] = None
    # ... other fields
```

#### 2. Full Phone Number Exposure
**File:** `backend/app/schemas/auth.py`
**Issue:** The `UserResponse` schema includes both `phone_number` (full) and `masked_phone`. The full phone number should only be exposed to:
- The user themselves
- Admin users with appropriate permissions
- Internal services

**Recommendation:** Use `masked_phone` by default in public responses. Create a separate `PrivateUserResponse` for admin/internal use that includes the full phone number.

**Fix:**
```python
class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    # phone_number: str  # Remove from public response
    masked_phone: str  # Use masked version
    role: UserRole
    # ... other fields

class PrivateUserResponse(UserResponse):
    """Extended response for admin/internal use"""
    phone_number: str  # Include full phone number
    national_id: Optional[str] = None  # Include for verification
    # ... other sensitive fields
```

### Medium Priority Issues

#### 3. Email Address Exposure
**File:** `backend/app/schemas/auth.py`
**Issue:** Email addresses are exposed in `UserResponse`. While less sensitive than national ID, email addresses should be protected.

**Recommendation:** Consider masking email addresses in public responses (e.g., `j***@example.com`).

#### 4. Location Data Exposure
**File:** `backend/app/schemas/auth.py`
**Issue:** The schema includes `province`, `district`, and `ward` which could be used for tracking.

**Recommendation:** This is acceptable for a marketplace platform (needed for logistics), but consider:
- Only exposing to relevant parties (buyer/seller in a transaction)
- Adding privacy controls for users who want to hide location

### Low Priority Issues

#### 5. Transaction Amounts
**File:** `backend/app/schemas/transaction.py`
**Issue:** Transaction amounts and fees are exposed in `OrderResponse`.

**Recommendation:** This is necessary for the marketplace functionality. However, consider:
- Only exposing transaction details to the parties involved
- Implementing privacy settings for users who want to hide transaction history

## Recommendations by Endpoint

### Authentication Endpoints

#### `/api/v1/auth/login`
**Current Response:** Returns full `UserResponse` with national_id
**Recommendation:** Return minimal user data (id, role, masked_phone) after login. Full profile should be fetched separately.

#### `/api/v1/auth/me`
**Current Response:** Returns full `UserResponse`
**Recommendation:** This is acceptable as it's the user's own data, but consider removing national_id.

### User Endpoints

#### `/api/v1/users/{user_id}`
**Current Response:** Returns full `UserResponse`
**Recommendation:** 
- For public access: Return minimal data (id, full_name, role, trust_score, masked_phone)
- For admin access: Return full `PrivateUserResponse`
- For self-access: Return full data except national_id

### Transaction Endpoints

#### `/api/v1/orders/{order_id}`
**Current Response:** Returns `OrderResponse` with buyer/seller IDs and contact reveals
**Recommendation:** 
- Only expose contact information to the parties involved in the transaction
- Implement conditional contact reveal based on order status

## Implementation Plan

### Phase 1: Critical Fixes (Immediate)
1. Remove `national_id` from `UserResponse` schema
2. Create `PrivateUserResponse` for admin/internal use
3. Update endpoints to use appropriate response schemas

### Phase 2: Medium Priority (1-2 weeks)
1. Implement email masking in public responses
2. Add privacy controls for location data
3. Update endpoint permissions to enforce data minimization

### Phase 3: Low Priority (1 month)
1. Review all other schemas for sensitive data
2. Implement data minimization across all endpoints
3. Add audit logging for sensitive data access

## Code Changes Required

### 1. Update auth.py Schema

```python
# backend/app/schemas/auth.py

class UserResponse(BaseModel):
    """Public user response with minimal data exposure"""
    id: uuid.UUID
    full_name: str
    masked_phone: str  # Only masked phone
    role: UserRole
    trust_score: int
    id_verified: bool
    # national_id removed
    email: Optional[str] = None  # Consider masking
    is_active: bool
    is_suspended: bool
    must_change_password: bool = False
    agent_status: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    preferred_language: Optional[str] = None
    notification_prefs: Optional[Dict[str, Any]] = None

class PrivateUserResponse(UserResponse):
    """Extended response for admin/internal use"""
    phone_number: str  # Full phone number
    national_id: Optional[str] = None  # For verification
    email: Optional[str] = None  # Full email
    # Add other sensitive fields as needed
```

### 2. Update Endpoint Dependencies

```python
# backend/app/api/deps.py

from app.schemas.auth import UserResponse, PrivateUserResponse

def get_public_user(db: Session, user_id: uuid.UUID) -> UserResponse:
    """Get public user data (minimal exposure)"""
    user = db.query(User).filter(User.id == user_id).first()
    return UserResponse.model_validate(user)

def get_private_user(db: Session, user_id: uuid.UUID) -> PrivateUserResponse:
    """Get private user data (admin/internal use only)"""
    user = db.query(User).filter(User.id == user_id).first()
    return PrivateUserResponse.model_validate(user)
```

### 3. Update Endpoints

```python
# backend/app/api/v1/endpoints/users.py

@router.get("/{user_id}", response_model=UserResponse)
def get_user_public(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """Public user endpoint - minimal data exposure"""
    return get_public_user(db, user_id)

@router.get("/{user_id}/admin", response_model=PrivateUserResponse)
def get_user_private(
    user_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Admin-only endpoint with full user data"""
    return get_private_user(db, user_id)
```

## Testing

### Test Cases

1. **Public user endpoint should not expose national_id**
```bash
curl https://api.zimagritrust.co.zw/api/v1/users/{user_id}
# Verify response does not contain national_id
```

2. **Admin endpoint should expose full data**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  https://api.zimagritrust.co.zw/api/v1/users/{user_id}/admin
# Verify response contains phone_number and national_id
```

3. **Login response should not expose national_id**
```bash
curl -X POST https://api.zimagritrust.co.zw/api/v1/auth/login \
  -d '{"phone_number":"+263123456789","password":"test"}'
# Verify response does not contain national_id
```

## Compliance Considerations

### GDPR (General Data Protection Regulation)
- **Right to minimization:** Only collect and expose data necessary for the purpose
- **Right to access:** Users should be able to see their own full data
- **Right to rectification:** Users should be able to correct their data

### POPIA (Protection of Personal Information Act - South Africa)
- Similar to GDPR, requires data minimization and purpose limitation
- Special protection for ID numbers and contact information

### Zimbabwe Data Protection
- While Zimbabwe doesn't have comprehensive data protection legislation yet
- Best practices should follow international standards

## Monitoring

### Audit Logging
Log all access to sensitive data:
```python
logger.info(
    "SENSITIVE_DATA_ACCESS",
    extra={
        "user_id": str(current_user.id),
        "target_user_id": str(target_user_id),
        "fields_accessed": ["national_id", "phone_number"],
        "endpoint": "/api/v1/users/{user_id}/admin",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
)
```

### Alerts
Set up alerts for:
- Unusual access to private user data
- Multiple failed attempts to access sensitive endpoints
- Access patterns that suggest data scraping

## Best Practices

1. **Default to minimal exposure:** Only expose data that is necessary for the use case
2. **Role-based access:** Different response schemas for different user roles
3. **Conditional exposure:** Only expose sensitive data when necessary (e.g., after payment confirmation)
4. **Audit everything:** Log all access to sensitive data
5. **Regular reviews:** Periodically review schemas for data exposure issues
6. **Privacy by design:** Build privacy controls into the system from the start

## Contact

For questions or issues with data exposure:
- Security Team: security@zimagritrust.co.zw
- Privacy Team: privacy@zimagritrust.co.zw

---

**Last Updated:** 2026-05-27
**Next Review:** 2026-06-27
