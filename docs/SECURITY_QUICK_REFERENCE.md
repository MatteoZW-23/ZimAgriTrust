# ZimAgriTrust Security - Quick Reference

## 10-Minute Quick Start

### 1. Install & Configure

```bash
# Install security packages
pip install -r requirements-security.txt

# Create .env file
cp .env.template .env

# Initialize database
python -m alembic upgrade head

# Seed roles
python scripts/seed_security.py

# Create the first super admin from the repo root
python backend/scripts/seed_super_admin.py

# Or bootstrap it via the API when the database has zero super admins
# POST /api/v1/super-admin/register-initial?username=...&email=...&password=...

# After the first root super admin exists, create more via:
# POST /api/v1/super-admin/accounts
# (requires a logged-in ROOT_SUPER_ADMIN and dual-control MFA)
```

### 2. Start Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Test PIN Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/pin \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+263771234567", "pin": "1234", "channel": "app"}'
```

---

## API Endpoints Reference

| Endpoint | Method | Purpose | Auth | Rate Limit |
|----------|--------|---------|------|-----------|
| `/api/v1/auth/login/pin` | POST | PIN login (USSD+App) | None | 5/hour |
| `/api/v1/auth/login/password` | POST | Password login | None | 5/hour |
| `/api/v1/auth/pin/change` | POST | Change PIN | Bearer | 5/hour |
| `/api/v1/auth/password/reset` | POST | Request reset | None | 3/hour |
| `/api/v1/auth/password/reset-confirm` | POST | Confirm reset | None | 3/hour |
| `/api/v1/auth/mfa/setup` | POST | Setup MFA | Bearer | 3/hour |
| `/api/v1/auth/mfa/verify` | POST | Verify MFA | Bearer | 10/hour |
| `/api/v1/auth/logout` | POST | Logout | Bearer | 10/hour |
| `/api/v1/auth/token/refresh` | POST | Refresh token | None | 100/min |
| `/api/v1/auth/register/farmer` | POST | Register farmer | None | 3/hour |
| `/api/v1/auth/register/buyer` | POST | Register buyer | None | 3/hour |
| `/api/v1/auth/register/driver` | POST | Register driver | None | 3/hour |
| `/api/v1/auth/invitation/accept` | POST | Accept invite | None | 3/hour |

---

## Request/Response Formats

### PIN Login

**Request**:
```json
{
  "phone_number": "+263771234567",
  "pin": "1234",
  "channel": "app"  // or "ussd"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### PIN Change

**Request**:
```json
{
  "current_pin": "1234",
  "new_pin": "5678",
  "new_pin_confirm": "5678"
}
```

**Response**:
```json
{
  "message": "PIN changed successfully",
  "notifications_sent": {
    "sms": true,
    "whatsapp": true,
    "email": true
  }
}
```

### MFA Setup

**Request**:
```json
{
  "method": "totp"  // or "hardware", "sms"
}
```

**Response**:
```json
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "backup_codes": [
    "XXXX-XXXX-XXXX",
    "YYYY-YYYY-YYYY",
    ...
  ],
  "setup_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## Security Constants

### PIN Rules

```python
PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 6
PIN_LOCKOUT_ATTEMPTS = 3
PIN_LOCKOUT_DURATION_MINUTES = 15
PIN_HISTORY_COUNT = 3  # Cannot reuse last 3

# Invalid PINs
INVALID_PATTERNS = [
    "1234",      # Sequential
    "2345",      # Sequential
    "1111",      # Repeated
    "2222",      # Repeated
    "1971",      # Birth year
    # Any part of phone number
    # Any part of phone digits
]
```

### Password Rules

```python
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_HISTORY_COUNT = 5
PASSWORD_EXPIRY_DAYS = 90
```

### Token Expiry (by Role)

```python
TOKEN_EXPIRY = {
    "access_token": {
        "SUPER_ADMIN": 15,      # 15 minutes
        "SYSTEM_ADMIN": 30,     # 30 minutes
        "FINANCE_ADMIN": 30,    # 30 minutes
        "AGENT": 480,           # 8 hours
        "FARMER": 480,          # 8 hours
    },
    "refresh_token": {
        "SUPER_ADMIN": 7,       # 7 days
        "FARMER": 30,           # 30 days
    }
}
```

### Rate Limits

```python
RATE_LIMITS = {
    "login": 5,           # 5 per hour
    "password_reset": 3,  # 3 per hour
    "pin_attempts": 5,    # 5 per hour
    "mfa": 10,            # 10 per hour
    "otp": 3,             # 3 per hour
    "api_general": 100,   # 100 per minute
}
```

---

## Using Security Features in Code

### 1. Verify PIN

```python
from app.services.security_service import PINManager

# Verify PIN
is_valid, error = PINManager.verify_pin(
    db=db,
    user=user,
    pin="1234",
    channel="app"  # or "ussd"
)

if not is_valid:
    raise HTTPException(status_code=401, detail=error)
```

### 2. Create Token

```python
from app.services.security_service import TokenManager

# Create access token
token, expiry = TokenManager.create_access_token(user)

# Create refresh token
refresh_token, refresh_expiry = TokenManager.create_refresh_token(user)

# Verify token
user_from_token = TokenManager.verify_token(db, token)
```

### 3. Manage Sessions

```python
from app.services.security_service import SessionManager

# Create session
session = SessionManager.create_session(
    db=db,
    user=user,
    access_token_hash="hash",
    refresh_token_hash="hash",
    ip_address="192.168.1.1",
    device_fingerprint="device_fp"
)

# Enforce concurrency limit
SessionManager.enforce_concurrency_limit(db, user)

# Terminate session
SessionManager.terminate_session(
    db=db,
    session_id=session.id,
    reason="logout"
)
```

### 4. Log Audit Event

```python
from app.services.security_service import AuditLogger
from app.models.security_enhanced import AuditLogAction

# Log action
AuditLogger.log(
    db=db,
    action=AuditLogAction.LOGIN,
    user_id=user.id,
    resource_type="user",
    resource_id=user.id,
    ip_address="192.168.1.1",
    details={"channel": "mobile"}
)
```

### 5. Send Notification

```python
from app.services.notification_service import NotificationService

# Send notification
await NotificationService.send_notification(
    db=db,
    user=user,
    template_key="PIN_CHANGED",
    old_pin="1234",
    new_pin="5678",
    timestamp="2026-05-06 10:30:00"
)
```

### 6. Check Permission

```python
from app.services.rbac_service import RBACService

# Check permission
if not RBACService.user_has_permission(db, user, "transaction:approve"):
    raise HTTPException(status_code=403, detail="Forbidden")

# Check resource access
can_access = RBACService.user_can_access_resource(
    db=db,
    user=user,
    resource_type="transaction",
    resource_owner_id=transaction.user_id
)
```

---

## Error Responses

### PIN Too Short

```json
{
  "detail": "PIN must be 4-6 digits"
}
```

### PIN Invalid Pattern

```json
{
  "detail": "PIN cannot be sequential digits"
}
```

### Account Locked

```json
{
  "detail": "Account locked due to too many failed attempts. Try again in 15 minutes."
}
```

### Rate Limit Exceeded

```json
{
  "detail": "Too many requests. Try again in 5 minutes."
}
```

### Invalid Token

```json
{
  "detail": "Invalid or expired token"
}
```

### Insufficient Permissions

```json
{
  "detail": "Insufficient permissions for this action"
}
```

---

## Database Schema Reference

### Key Tables

```sql
-- PIN Management
pin_history         -- Track PIN changes
pin_lockout         -- Track failed attempts & lockouts
pin_attempt         -- Audit trail of all PIN attempts

-- Session Management
user_session        -- Active sessions with device tracking

-- Token Management
token_blacklist     -- Revoked tokens

-- MFA
mfa_configuration   -- TOTP secrets, backup codes

-- Security
security_threat     -- Detected threats
audit_log           -- Immutable audit trail
rate_limit          -- Request rate tracking

-- Notifications
notification_log    -- Delivery tracking
notification_preference -- User preferences
```

### Important Indexes

```sql
-- For quick PIN lookup
CREATE INDEX idx_pin_lockout_user ON pin_lockout(user_id);

-- For session queries
CREATE INDEX idx_user_session_active ON user_session(user_id, status);

-- For rate limiting
CREATE INDEX idx_rate_limit_window ON rate_limit(identifier, expires_at);

-- For audit queries
CREATE INDEX idx_audit_log_action ON audit_log(user_id, action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
```

---

## Troubleshooting

### PIN Locked?

```python
# Admin unlock
from app.models.security_enhanced import PINLockout

lockout = db.query(PINLockout).filter(
    PINLockout.user_id == user_id
).first()

if lockout:
    lockout.failed_attempts = 0
    lockout.locked_until = None
    db.commit()
```

### Token Expired?

```bash
# Generate new token using refresh token
curl -X POST http://localhost:8000/api/v1/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Rate Limited?

```python
# Check rate limit status
from app.services.security_service import RateLimiter

is_allowed, remaining = RateLimiter.check_limit(
    db=db,
    identifier=user_id,
    key="login_attempts"
)
```

### Notifications Not Sending?

```python
# Check if adapters initialized
from app.services.notification_service import NotificationService

# Initialize mock adapters for testing
NotificationService.initialize(
    sms_adapter=MockSMSAdapter(),
    whatsapp_adapter=MockWhatsAppAdapter(),
    email_adapter=MockEmailAdapter()
)
```

---

## Configuration Checklist

Before deploying, verify:

```
[ ] SECRET_KEY set and unique
[ ] PIN_PEPPER set and unique
[ ] DATABASE_URL points to production DB
[ ] REDIS_URL configured for rate limiting
[ ] SMS_API_KEY and credentials
[ ] WHATSAPP_API_KEY and phone ID
[ ] SENDGRID_API_KEY configured
[ ] HTTPS/TLS enabled in production
[ ] Security headers enabled
[ ] CORS origins whitelist set
[ ] Audit logging enabled
[ ] Rate limits configured
[ ] MFA required for admins
[ ] Backup procedures scheduled
```

---

## Helpful Commands

```bash
# Check PIN rules
python -c "from app.services.security_service import PINValidator; print(PINValidator.validate('1234'))"

# Hash a password
python -c "from app.services.security_service import PasswordHasher; print(PasswordHasher.hash_password('MyPassword123!'))"

# Generate secret
python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"

# Check token
python -c "from app.services.security_service import TokenManager; print(TokenManager.verify_token(db, 'token'))"

# List active sessions
python -c "from app.models.security_enhanced import UserSession; print(db.query(UserSession).filter(UserSession.status='ACTIVE').all())"

# Check audit log
python -c "from app.models.security_enhanced import AuditLog; print(db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all())"
```

---

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `security_enhanced.py` | Database models | 450 |
| `security_service.py` | Security logic | 700 |
| `rbac_service.py` | Permissions | 350 |
| `notification_service.py` | Notifications | 400 |
| `invitation_service.py` | Invitations | 200 |
| `auth.py` | API endpoints | 600 |
| `config.py` | Configuration | +100 |

---

## Performance Tips

1. **Use Redis** for rate limiting (100x faster than DB)
2. **Cache tokens** in memory (< 1ms lookup)
3. **Batch audit logs** (every 100 records or 5 seconds)
4. **Index PIN & session tables** (see schema above)
5. **Use connection pooling** (10-20 connections)
6. **Monitor response times** (log > 500ms)

---

## Contact

- **Questions?** security@zimagritrust.co.zw
- **Issues?** Create GitHub issue or email
- **Urgent?** Call +263 (0) 1 XXX XXXX (24/7)

---

**Last Updated**: May 6, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
