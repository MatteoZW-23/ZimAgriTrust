# ZimAgriTrust — Authentication & Security Framework

## Overview

Complete zero-trust authentication and security architecture with 12 user roles, RBAC, MFA, tamper-proof audit logging, and role-based session management.

---

## 1. User Roles & Hierarchy

| Level | Role | Auth Method | MFA | Onboarding |
|-------|------|-------------|-----|------------|
| 100 | `SUPER_ADMIN` | Email + Password + Hardware | Required | DB seed |
| 100 | `ADMIN` (legacy) | Email + Password + TOTP | Required | DB seed |
| 90 | `SYSTEM_ADMIN` | Email + Password + TOTP | Required | Invitation |
| 85 | `FINANCE_ADMIN` | Email + Password + TOTP | Required | Invitation |
| 80 | `REGIONAL_ADMIN` | Email + Password + TOTP | Required | Invitation |
| 80 | `REGIONAL_MANAGER` (legacy) | Email + Password + TOTP | Required | Invitation |
| 75 | `SUPPORT_ADMIN` | Email + Password | Optional | Invitation |
| 70 | `BRANCH_ADMIN` | Email + Password | Optional | Invitation |
| 60 | `SUPPLIER` | Email + Password | No | Self-reg + approval |
| 40 | `AGENT` | Agent Code + PIN | No | Invitation + Academy |
| 30 | `STAFF` | Email + Password | Optional | Invitation |
| 20 | `DRIVER`/`TRANSPORTER` | Phone + PIN | No | Self-reg + approval |
| 10 | `FARMER` | Phone + PIN (unified) | No | Self-registration |
| 10 | `BUYER` | Phone + PIN (unified) | No | Self-registration |

**Files:**
- `backend/app/models/user.py` — `UserRole` enum
- `backend/app/models/security_enhanced.py` — `RoleLevel` enum
- `backend/app/services/rbac_service.py` — permission registry + role levels

---

## 2. Authentication Flows

### 2.1 Farmer/Buyer — PIN Login
```
POST /api/v1/auth/app/login
Body: { "phone_number": "+263...", "password": "1234" }
→ JWT access + refresh tokens, HTTP-only cookies
```

### 2.2 Driver — OTP Registration + PIN Login
```
POST /api/v1/auth/driver/request-otp   → sends OTP
POST /api/v1/auth/driver/verify-otp    → temp registration token
POST /api/v1/drivers/self-register     → creates account (pending approval)
POST /api/v1/auth/driver/login         → PIN login after approval
```

### 2.3 Supplier — Email + Password
```
POST /api/v1/auth/supplier/login
Body: { "email": "...", "password": "..." }
```

### 2.4 Staff — Email + Password (+ optional MFA)
```
POST /api/v1/auth/staff/login
Body: { "email": "...", "password": "..." }
→ If MFA enabled: returns { status: "MFA_REQUIRED" }
→ If MFA setup needed: returns { status: "MFA_SETUP_REQUIRED" }
```

### 2.5 Admin — Password + MFA (2-step)
```
POST /api/v1/admin/login           → Step 1: password check → sends OTP
POST /api/v1/admin/verify-mfa      → Step 2: OTP verification → JWT tokens
```

### 2.6 Agent — Password + MFA (2-step)
```
POST /api/v1/agent/login           → Step 1: password check → sends OTP
POST /api/v1/agent/verify-mfa      → Step 2: OTP verification → JWT tokens
```

---

## 3. MFA (Multi-Factor Authentication)

### TOTP Setup Flow
```
GET  /api/v1/auth/mfa/status           → Check MFA status
POST /api/v1/auth/mfa/setup            → Get QR code + secret
POST /api/v1/auth/mfa/setup/confirm    → Verify first code → get backup codes
POST /api/v1/auth/mfa/verify           → Verify TOTP or backup code
POST /api/v1/auth/mfa/backup-codes/regenerate → New backup codes
POST /api/v1/auth/mfa/disable          → Disable (if optional)
```

**Files:**
- `backend/app/services/mfa_service.py` — `MFAService` class
- `backend/app/api/v1/endpoints/security_auth.py` — MFA endpoints
- `backend/app/models/security_enhanced.py` — `MFAConfiguration`, `MFAAttempt`

---

## 4. PIN Security

### Validation Rules
- 4-6 digits only
- No sequential: 1234, 2345, 3456, etc.
- No repeated: 1111, 2222, etc.
- Cannot contain phone number digits
- Cannot contain birth year
- Cannot reuse last 3 PINs

### PIN Change
```
POST /api/v1/auth/security/change-pin
Body: { "current_pin": "1234", "new_pin": "5678" }
→ Validates rules + history, terminates all other sessions
```

**Files:**
- `backend/app/services/pin_validator.py` — `PINValidator` class
- `backend/app/models/security_enhanced.py` — `PINHistory`, `PINLockout`, `PINAttempt`

---

## 5. Password Security

### Requirements (Admins, Suppliers, Staff)
- Min 12 characters
- 1 uppercase, 1 lowercase, 1 digit, 1 special character
- Not in common password list
- Cannot reuse last 5 passwords
- 90-day expiry for admins

### Password Change
```
POST /api/v1/auth/security/change-password
Body: { "current_password": "...", "new_password": "..." }
→ Validates strength + history, terminates all other sessions
```

**Files:**
- `backend/app/core/password_validator.py` — `PasswordValidator` class
- `backend/app/models/security_enhanced.py` — `PasswordHistory`

---

## 6. Session Management

### Role-Based Timeouts

| Role | Access Token | Refresh Token | Max Sessions |
|------|-------------|---------------|-------------|
| SUPER_ADMIN | 15 min | 7 days | 1 |
| SYSTEM_ADMIN | 30 min | 7 days | 2 |
| FINANCE_ADMIN | 30 min | 7 days | 2 |
| REGIONAL_ADMIN | 30 min | 7 days | 3 |
| SUPPORT_ADMIN | 60 min | 14 days | 5 |
| BRANCH_ADMIN | 60 min | 14 days | 5 |
| SUPPLIER | 60 min | 30 days | 5 |
| AGENT | 8 hours | 30 days | 1 |
| STAFF | 60 min | 14 days | 3 |
| DRIVER | 60 min | 30 days | 1 |
| FARMER | 60 min | 30 days | Unlimited |
| BUYER | 60 min | 30 days | Unlimited |

### Endpoints
```
GET  /api/v1/auth/security/sessions        → List active sessions
POST /api/v1/auth/security/sessions/revoke  → Revoke specific session
POST /api/v1/auth/security/sessions/revoke-all → Revoke all except current
POST /api/v1/auth/security/logout           → Logout + clear cookies
```

**Files:**
- `backend/app/services/portal_auth_service.py` — `ACCESS_TOKEN_EXPIRY_BY_ROLE`, `REFRESH_TOKEN_EXPIRY_DAYS_BY_ROLE`
- `backend/app/services/session_service.py` — Session CRUD
- `backend/app/services/security_service.py` — `SessionManager`

---

## 7. Rate Limiting

Redis-backed rate limiting per endpoint category and role.

| Category | Limit |
|----------|-------|
| Login attempts | 5/hour (unauthenticated) |
| PIN attempts | 5/hour (locked after 3) |
| MFA verification | 10/hour |
| OTP requests | 3/hour |
| API general | 100/minute |

**Files:**
- `backend/app/services/rate_limit_service.py`
- `backend/app/core/security_middleware.py` — `SecurityMiddleware._check_rate_limit()`

---

## 8. Audit Logging

### Tamper-Proof Chain
Every financial event appends to `audit_checksums` with HMAC-SHA256 chain linking.

### Security Audit Log
All auth events logged to `security_audit_logs`: login, logout, PIN change, password change, MFA enable/disable, role change, etc.

**Files:**
- `backend/app/services/audit_chain_service.py` — `append_audit()`, `verify_chain()`
- `backend/app/models/security_enhanced.py` — `SecurityAuditLog`, `AuditLogAction`
- `backend/app/models/security.py` — `AuditChecksum`, `AdminActionLog`

---

## 9. Security Middleware

Applied globally via `SecurityMiddleware`:

| Protection | Header/Method |
|------------|---------------|
| HSTS | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| No sniff | `X-Content-Type-Options: nosniff` |
| Clickjack | `X-Frame-Options: DENY` |
| CSP | `Content-Security-Policy: default-src 'self'...` |
| Referrer | `Referrer-Policy: strict-origin-when-cross-origin` |
| CSRF | Token in cookie + header comparison |
| Scanner block | Blocks sqlmap, nmap, nikto, burpsuite UAs |
| IP whitelist | Admin endpoints restricted by IP |
| Rate limiting | Per-IP, per-endpoint |

**Files:**
- `backend/app/core/security_middleware.py`
- `backend/app/main.py` — middleware registration

---

## 10. Invitation System

For privileged roles (SYSTEM_ADMIN through STAFF):

```
POST /api/v1/admin/invite   → Create invitation (72h expiry)
GET  /api/v1/auth/invite/verify?token=...&email=...
POST /api/v1/auth/invite/accept
```

**Files:**
- `backend/app/services/invitation_service.py`
- `backend/app/models/rbac.py` — `Invitation`, `InvitationStatus`

---

## 11. Emergency Procedures

### Emergency Shutdown
- `EmergencyShutdownMiddleware` checks `SYSTEM_LOCKDOWN` config
- All write operations blocked except super-admin
- Triggered via `POST /api/v1/super-admin/emergency-shutdown`

### Breach Response
1. Automatic detection via anomaly middleware
2. Affected accounts suspended
3. Password/PIN reset forced
4. Audit logs preserved
5. Users notified via SMS + WhatsApp

**Files:**
- `backend/app/main.py` — `EmergencyShutdownMiddleware`
- `backend/app/api/v1/endpoints/super_admin.py`

---

## 12. API Endpoint Summary

### Auth Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/app/login` | Farmer/Buyer PIN login |
| POST | `/api/v1/auth/driver/login` | Driver PIN login |
| POST | `/api/v1/auth/driver/request-otp` | Driver registration OTP |
| POST | `/api/v1/auth/driver/verify-otp` | Verify driver OTP |
| POST | `/api/v1/auth/supplier/login` | Supplier email+password |
| POST | `/api/v1/auth/staff/login` | Staff email+password (+MFA) |
| POST | `/api/v1/admin/login` | Admin password+MFA step 1 |
| POST | `/api/v1/admin/verify-mfa` | Admin MFA step 2 |
| POST | `/api/v1/agent/login` | Agent password+MFA step 1 |
| POST | `/api/v1/agent/verify-mfa` | Agent MFA step 2 |

### Security Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/security/change-pin` | Change PIN |
| POST | `/api/v1/auth/security/change-password` | Change password |
| POST | `/api/v1/auth/security/logout` | Logout |
| GET | `/api/v1/auth/security/sessions` | List sessions |
| POST | `/api/v1/auth/security/sessions/revoke` | Revoke session |
| POST | `/api/v1/auth/security/sessions/revoke-all` | Revoke all sessions |

### MFA Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/auth/mfa/status` | MFA status |
| POST | `/api/v1/auth/mfa/setup` | Begin TOTP setup |
| POST | `/api/v1/auth/mfa/setup/confirm` | Confirm with first code |
| POST | `/api/v1/auth/mfa/verify` | Verify TOTP/backup code |
| POST | `/api/v1/auth/mfa/backup-codes/regenerate` | New backup codes |
| POST | `/api/v1/auth/mfa/disable` | Disable MFA |
