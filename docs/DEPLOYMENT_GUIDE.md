# ZimAgriTrust Security System - Deployment & Integration Guide

## Quick Start Guide

### Phase 1: Setup & Installation (Day 1)

#### 1.1 Install Security Dependencies

```bash
# From backend directory
pip install -r requirements.txt
pip install -r requirements-security.txt
```

#### 1.2 Update Environment Configuration

Create/update `.env` file in backend root:

```env
# ============================================================================
# JWT & TOKEN CONFIGURATION
# ============================================================================
SECRET_KEY=generate-high-entropy-secret-with-secrets.token_urlsafe(32)
REFRESH_SECRET_KEY=generate-another-secret
ALGORITHM=HS256

# ============================================================================
# PIN SECURITY (Unified USSD + App)
# ============================================================================
PIN_MIN_LENGTH=4
PIN_MAX_LENGTH=6
PIN_PEPPER=generate-pin-pepper-with-secrets.token_urlsafe(32)
PIN_LOCKOUT_ATTEMPTS=3
PIN_LOCKOUT_DURATION_MINUTES=15
PIN_HISTORY_COUNT=3

# ============================================================================
# PASSWORD REQUIREMENTS (Admins & Staff)
# ============================================================================
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_HISTORY_COUNT=5
PASSWORD_EXPIRY_DAYS=90

# ============================================================================
# RATE LIMITING
# ============================================================================
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_PASSWORD_RESET=3
RATE_LIMIT_PIN_ATTEMPTS=5
RATE_LIMIT_MFA_ATTEMPTS=10
RATE_LIMIT_OTP_REQUESTS=3

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================
SESSION_ABSOLUTE_TIMEOUT_MINUTES=480
SESSION_IDLE_TIMEOUT_MINUTES=60
MAX_CONCURRENT_SESSIONS=5

# ============================================================================
# MFA CONFIGURATION
# ============================================================================
MFA_REQUIRED_ROLES=SUPER_ADMIN,SYSTEM_ADMIN,FINANCE_ADMIN
TOTP_WINDOW=1
BACKUP_CODES_COUNT=10

# ============================================================================
# NOTIFICATIONS (Multi-Channel)
# ============================================================================
SMS_API_KEY=your-africas-talking-api-key
SMS_USERNAME=sandbox
SMS_SENDER_ID=ZimAgriTrust
SMS_ENABLE=true

WHATSAPP_API_KEY=your-whatsapp-business-api-key
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ENABLE=true

EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-sendgrid-api-key
EMAIL_FROM_ADDRESS=security@zimagritrust.co.zw
EMAIL_ENABLE=true

# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================
INVITATION_ENABLED=true
INVITATION_EXPIRY_HOURS=72
RBAC_ENABLED=true

# ============================================================================
# FRONTEND URLS
# ============================================================================
FRONTEND_URL=http://localhost:3000
ADMIN_DASHBOARD_URL=http://localhost:3001
AGENT_PORTAL_URL=http://localhost:3002
```

#### 1.3 Initialize Database Schema

```bash
# Apply migrations for security tables
python -m alembic upgrade head

# Or manually create tables
python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
```

#### 1.4 Seed Default Roles & Permissions

```python
# Create script: scripts/seed_security.py
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.rbac_service import RBACService

db = SessionLocal()
RBACService.create_default_roles(db)
db.close()

print("✅ Default roles and permissions seeded successfully")
```

Run it:
```bash
python scripts/seed_security.py
```

#### 1.5 Create Super Admin Account

```python
# Create script: scripts/create_super_admin.py
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.services.security_service import PasswordHasher
from app.models.security_enhanced import MFAConfiguration, MFAStatus
import uuid

def create_super_admin():
    email = "admin@zimagritrust.co.zw"
    password = "TemporarySecurePassword123!"
    
    db = SessionLocal()
    
    # Check if exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"❌ User already exists: {email}")
        return
    
    # Hash password
    pw_hasher = PasswordHasher()
    password_hash = pw_hasher.hash_password(password)
    
    # Create user
    user = User(
        id=uuid.uuid4(),
        email=email,
        full_name="System Administrator",
        password_hash=password_hash,
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        is_phone_verified=True,
        email_verified=True,
    )
    
    db.add(user)
    db.flush()
    
    # Create MFA config
    mfa_config = MFAConfiguration(
        user_id=user.id,
        status=MFAStatus.DISABLED,  # Can be setup after first login
    )
    db.add(mfa_config)
    
    db.commit()
    
    print(f"""
    ✅ Super Admin created successfully!
    
    Email: {email}
    Password: {password}
    
    ⚠️  IMPORTANT: 
    1. Change this password immediately after first login
    2. Setup MFA (TOTP or YubiKey) for security
    3. Delete this script after running
    """)
    
    db.close()

if __name__ == "__main__":
    create_super_admin()
```

Run it:
```bash
python scripts/create_super_admin.py
```

### Phase 2: Integration with API (Day 2)

#### 2.1 Update Main App to Use Security

Edit `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.core.security_middleware import apply_security_middleware
from app.api.v1.auth import router as auth_router
from app.core.config import settings

app = FastAPI(title="ZimAgriTrust")

# Apply security middleware
apply_security_middleware(app)

# Register routers
app.include_router(auth_router)

# Initialize notification service adapters
from app.services.notification_service import NotificationService, MockSMSAdapter, MockWhatsAppAdapter, MockEmailAdapter

NotificationService.initialize(
    sms_adapter=MockSMSAdapter() if not settings.SMS_ENABLE else None,
    whatsapp_adapter=MockWhatsAppAdapter() if not settings.WHATSAPP_ENABLE else None,
    email_adapter=MockEmailAdapter() if not settings.EMAIL_ENABLE else None,
)

@app.on_event("startup")
async def startup():
    print("🔐 Security system initialized")
    print("✅ Authentication endpoints ready")
    print("✅ Notification service ready")
    print("✅ Rate limiting active")
```

#### 2.2 Add Security Headers Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

#### 2.3 Update Existing Auth Endpoints

If you have existing auth endpoints, update them to use the new security services:

```python
from app.services.security_service import PINManager, SessionManager, TokenManager
from app.models.security_enhanced import AuditLog, AuditLogAction

# Example: Update existing PIN login endpoint
@app.post("/api/v1/auth/login")
async def login(phone: str, pin: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == phone).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify PIN using unified system
    is_valid, error = PINManager.verify_pin(db, user, pin, channel="app")
    
    if not is_valid:
        raise HTTPException(status_code=401, detail=error)
    
    # Create tokens
    access_token, _ = TokenManager.create_access_token(user)
    refresh_token, _ = TokenManager.create_refresh_token(user)
    
    # Create session
    SessionManager.create_session(
        db, user,
        hashlib.sha256(access_token.encode()).hexdigest(),
        hashlib.sha256(refresh_token.encode()).hexdigest(),
        request.client.host,
        "fingerprint_here",
    )
    
    # Log audit
    AuditLogger.log(db, AuditLogAction.LOGIN, user_id=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
```

### Phase 3: Testing Security Features (Day 3)

#### 3.1 Test PIN Management

```bash
# Test PIN login
curl -X POST http://localhost:8000/api/v1/auth/login/pin \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+263771234567",
    "pin": "1234",
    "channel": "app"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 3.2 Test PIN Change

```bash
# Change PIN (unified across USSD and App)
curl -X POST http://localhost:8000/api/v1/auth/pin/change \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "current_pin": "1234",
    "new_pin": "5678",
    "new_pin_confirm": "5678"
  }'

# Response:
{
  "message": "PIN changed successfully",
  "notifications_sent": {
    "sms": true,
    "whatsapp": true,
    "email": true
  }
}
```

#### 3.3 Test MFA Setup

```bash
# Setup TOTP MFA
curl -X POST http://localhost:8000/api/v1/auth/mfa/setup \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"method": "totp"}'

# Response:
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "backup_codes": [
    "XXXX-XXXX-XXXX",
    "YYYY-YYYY-YYYY",
    ...
  ],
  "setup_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 3.4 Test Rate Limiting

```bash
# Test rate limiting (make 6 login attempts to hit limit)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/pin \
    -H "Content-Type: application/json" \
    -d '{"phone_number": "+263771234567", "pin": "wrong"}' 2>/dev/null
  echo ""
done

# Last request should return 429 Too Many Requests
```

#### 3.5 Test Notifications

```bash
# Trigger a notification (PIN change)
curl -X POST http://localhost:8000/api/v1/auth/pin/change \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"current_pin": "5678", "new_pin": "1111", "new_pin_confirm": "1111"}'

# Check logs for SMS, WhatsApp, Email delivery
# In console/mock mode, you'll see:
# [SMS] +263771234567: Your PIN was changed...
# [WHATSAPP] +263771234567: ⚠️ Your PIN was recently changed...
# [EMAIL] user@example.com | PIN Changed
```

### Phase 4: Production Deployment

#### 4.1 Secrets Management

```bash
# Generate secure secrets
python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"

# Store in secure secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
# Never commit .env to Git
```

#### 4.2 Enable Production Notifications

Update `.env`:

```env
# Real SMS (Africa's Talking)
SMS_ENABLE=true
SMS_USERNAME=your-africas-talking-username
SMS_API_KEY=your-api-key

# Real WhatsApp (WhatsApp Business API)
WHATSAPP_ENABLE=true
WHATSAPP_API_KEY=your-whatsapp-key
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

# Real Email (SendGrid)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-sendgrid-key
```

Implement real adapters:

```python
# app/services/adapters/sms_africas_talking.py
class AfricasTalkingSMSAdapter(SMSAdapter):
    async def send(self, phone: str, message: str) -> Dict:
        # Implement Africa's Talking API call
        pass

# app/services/adapters/whatsapp_business.py
class WhatsAppBusinessAdapter(WhatsAppAdapter):
    async def send(self, phone: str, message: str) -> Dict:
        # Implement WhatsApp Business API call
        pass

# app/services/adapters/sendgrid_email.py
class SendGridEmailAdapter(EmailAdapter):
    async def send(self, email: str, subject: str, body: str) -> Dict:
        # Implement SendGrid API call
        pass
```

#### 4.3 Enable Redis for Production Rate Limiting

```bash
# Install Redis
docker run -d -p 6379:6379 redis:latest

# Or on production server:
sudo apt-get install redis-server
sudo systemctl start redis-server
```

Update `.env`:

```env
REDIS_URL=redis://production-redis-host:6379/0
```

#### 4.4 Database Backups

```bash
# Backup security tables daily
pg_dump -U postgres -d zimagritrust -t "user_sessions" \
  -t "token_blacklist" \
  -t "audit_logs" \
  -t "security_threats" \
  > backups/security_$(date +%Y%m%d).sql

# Automate with cron:
0 2 * * * /path/to/backup_security.sh
```

#### 4.5 Monitoring & Alerts

Set up alerts for:

```
- 5+ failed login attempts from same IP
- PIN lockout events
- Suspicious activity detection
- Token blacklist overflow
- Session anomalies
- Rate limit violations
```

### Phase 5: Continuous Maintenance

#### 5.1 Daily Tasks

- [ ] Review security threat dashboard
- [ ] Check failed authentication attempts
- [ ] Monitor rate limit violations
- [ ] Review audit logs for suspicious patterns

#### 5.2 Weekly Tasks

- [ ] Rotate MFA backup codes (if used)
- [ ] Review user session activity
- [ ] Check password expiry reminders
- [ ] Verify notification delivery status

#### 5.3 Monthly Tasks

- [ ] Full security audit
- [ ] Review and update rate limits
- [ ] Check for compromised credentials
- [ ] Update security patches
- [ ] Review RBAC assignments

#### 5.4 Quarterly Tasks

- [ ] Penetration testing
- [ ] Security training for admins
- [ ] Review and update security policies
- [ ] Rotate all secrets/keys
- [ ] Disaster recovery drill

---

## Troubleshooting Common Issues

### Issue 1: PIN Lockout

**Problem**: User gets locked out after 3 failed attempts

**Solution**:
```python
from app.models.security_enhanced import PINLockout
from sqlalchemy.orm import Session

def unlock_pin(db: Session, user_id):
    lockout = db.query(PINLockout).filter(PINLockout.user_id == user_id).first()
    if lockout:
        lockout.failed_attempts = 0
        lockout.locked_until = None
        db.commit()
        print("✅ PIN lockout cleared")
```

### Issue 2: Session Timeout Too Short

**Problem**: Users get logged out too quickly

**Solution**: Adjust in `.env`:

```env
SESSION_IDLE_TIMEOUT_MINUTES=120  # Increase from 60
SESSION_ABSOLUTE_TIMEOUT_MINUTES=1440  # 24 hours
```

### Issue 3: Rate Limiting Too Strict

**Problem**: Legitimate users hitting rate limits

**Solution**: Adjust limits in `.env`:

```env
RATE_LIMIT_LOGIN_ATTEMPTS=10  # Increase from 5
RATE_LIMIT_PIN_ATTEMPTS=10  # Increase from 5
```

### Issue 4: MFA Setup Fails

**Problem**: TOTP QR code not generating

**Solution**: Ensure `qrcode` library installed:

```bash
pip install qrcode[pil]
```

---

## Support & Resources

- **Documentation**: `/docs/SECURITY_IMPLEMENTATION.md`
- **API Reference**: `/docs/api_reference.md`
- **Code Examples**: `/scripts/examples/`
- **Security Issues**: security@zimagritrust.co.zw
- **24/7 Support**: +263 (0) 1 XXX XXXX

---

## Checklist: Security System Ready

- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Database schema initialized
- [ ] Default roles seeded
- [ ] Super admin created
- [ ] API tests passing
- [ ] Notifications sending
- [ ] Rate limiting working
- [ ] Audit logging enabled
- [ ] MFA functioning
- [ ] PIN system unified (USSD + App)
- [ ] Session management active
- [ ] Security headers applied
- [ ] CORS configured
- [ ] Redis connected (if used)

✅ **Security system is production-ready!**
