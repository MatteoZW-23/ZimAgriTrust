# ZimAgriTrust Security Implementation Summary

## Overview
ZimAgriTrust has a comprehensive security architecture with multiple layers of protection. This document summarizes the current security implementation and recent enhancements.

## Current Security Features

### Authentication & Authorization
- **JWT Tokens**: Role-based token expiry (15min for super-admin, 8hrs for agents, 1hr for most roles)
- **PIN System**: bcrypt + pepper hashing for USSD/App users
- **Password Security**: Argon2id/bcrypt hashing with history enforcement (last 5 passwords)
- **RBAC**: Granular permissions (100+ permissions) with hierarchical role structure
- **MFA**: TOTP (authenticator app) with backup codes for privileged roles
- **Session Management**: Device fingerprinting, concurrent session limits, token blacklisting

### API Security
- **CORS**: Restricted to specific frontend origins (no wildcard)
- **Security Middleware**: 
  - Scanner/suspicious UA detection
  - Admin IP whitelisting
  - Request size limits (5-10MB)
  - Content-Type validation
  - CSRF token validation
  - Rate limiting (Redis with in-memory fallback)
  - Anomaly detection
- **Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **TrustedHost**: Host header validation
- **HTTPS Redirect**: Optional in production

### Database & Secrets
- **Secret Keys**: JWT signing keys (must be changed from defaults)
- **PIN Pepper**: Additional secret for PIN hashing
- **Transaction Signing**: HMAC keys for financial integrity
- **Audit Chain**: Tamper-proof audit checksum chain

### Monitoring & Audit
- **Audit Logging**: All admin operations logged
- **Security Audit Log**: Security events (MFA, password changes, threats)
- **Sentry Integration**: Error tracking
- **Metrics**: Performance monitoring
- **Emergency Shutdown**: Platform-wide lockdown capability

### Fraud Detection
- **Velocity Checks**: Multiple withdrawals in short time window
- **Structuring Detection**: Transactions just below limits
- **Trust Score**: ML-based risk assessment
- **New User Limits**: Restrictions for new accounts

## Recent Security Enhancements

### 1. CORS Restriction (Completed)
**Before**: Wildcard `allow_origins=["*"]`
**After**: Specific origins from config
```python
CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004"
```

### 2. Secret Key Warnings (Completed)
Updated default secret keys to indicate they must be changed:
- `SECRET_KEY`: "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"
- `REFRESH_SECRET_KEY`: "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"
- `PIN_PEPPER`: "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"

### 3. Redis-based Rate Limiting (Completed)
Updated rate limiting to use Redis for distributed deployments with in-memory fallback:
```python
# Try Redis first for distributed rate limiting
try:
    key = f"rate_limit:{client_ip}:{request.url.path}"
    count = await cache_service.increment_counter(key, window)
    if count and int(count) > limit:
        return False
    return True
except Exception as e:
    # Fallback to in-memory for single-instance deployments
```

### 4. MFA Enforcement (Completed)
Added TOTP MFA enforcement for required roles in login flow:
- Checks if MFA is required for user's role
- Returns `MFA_SETUP_REQUIRED` if MFA not set up
- Returns `TOTP_REQUIRED` if TOTP is enabled
- Falls back to OTP-based 2FA for non-MFA users
- Supports both TOTP and OTP verification in `complete_mfa_login`

## Security Configuration

### Required Environment Variables for Production
```bash
# JWT Keys (MUST CHANGE)
SECRET_KEY=your-high-entropy-secret-key
REFRESH_SECRET_KEY=your-different-high-entropy-secret-key

# PIN Hashing
PIN_PEPPER=your-pepper-secret

# CORS Origins
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# Admin IP Whitelist (optional but recommended)
ADMIN_IP_WHITELIST=1.2.3.4,5.6.7.8
SUPER_ADMIN_IP_WHITELIST=9.10.11.12

# MFA (already configured)
MFA_REQUIRED_ROLES=['SUPER_ADMIN','ADMIN','SYSTEM_ADMIN','FINANCE_ADMIN','REGIONAL_ADMIN','REGIONAL_MANAGER']
```

### Rate Limiting Configuration
```python
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_WINDOW_SECONDS: int = 60
RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # per hour
RATE_LIMIT_PASSWORD_RESET: int = 3  # per hour
RATE_LIMIT_PIN_ATTEMPTS: int = 5  # per hour
RATE_LIMIT_MFA_ATTEMPTS: int = 10  # per hour
RATE_LIMIT_OTP_REQUESTS: int = 3  # per hour
RATE_LIMIT_API_GENERAL: int = 100  # per minute
```

## MFA Required Roles
- SUPER_ADMIN
- ADMIN
- SYSTEM_ADMIN
- FINANCE_ADMIN
- REGIONAL_ADMIN
- REGIONAL_MANAGER

## MFA Optional Roles
- SUPPORT_ADMIN
- BRANCH_ADMIN
- STAFF

## Session Timeout by Role
- SUPER_ADMIN: 15 minutes
- SYSTEM_ADMIN: 30 minutes
- FINANCE_ADMIN: 30 minutes
- REGIONAL_ADMIN: 30 minutes
- SUPPORT_ADMIN: 60 minutes
- BRANCH_ADMIN: 60 minutes
- AGENT: 480 minutes (8 hours)
- STAFF: 60 minutes
- FARMER: 60 minutes
- BUYER: 60 minutes
- DRIVER: 60 minutes

## Pending Security Improvements

### 1. Frontend Session Timeout (In Progress)
Add auto-logout functionality to frontend apps when session expires:
- Monitor token expiry
- Show warning before expiry
- Auto-logout and redirect to login
- Implement in all frontend portals

### 2. Secrets Management (Recommended)
Integrate with secrets manager (HashiCorp Vault, AWS Secrets Manager) instead of environment variables:
- Rotate secrets automatically
- Audit secret access
- Secure secret distribution

### 3. Field-Level Encryption (Recommended)
Encrypt sensitive PII in database:
- Phone numbers
- Addresses
- National IDs
- Bank account details

### 4. IP Geolocation (Optional)
Add IP geolocation for security:
- Detect location changes
- Alert on suspicious login locations
- Geo-fencing for admin accounts

### 5. WebAuthn (Optional)
Add hardware key support for MFA:
- YubiKey
- WebAuthn/FIDO2
- Biometric authentication

## Security Best Practices

### Before Production Deployment
1. Change all default secret keys
2. Set up proper CORS origins
3. Configure admin IP whitelists
4. Enable HTTPS redirect
5. Set up Sentry for error tracking
6. Configure Redis for rate limiting
7. Review and adjust rate limit thresholds
8. Enable audit logging
9. Set up monitoring and alerts
10. Test MFA flow for required roles

### Regular Security Maintenance
- Review audit logs weekly
- Monitor failed login attempts
- Check for security threats in logs
- Update dependencies regularly
- Review and update RBAC permissions
- Test disaster recovery procedures
- Review and rotate secrets quarterly

## Security Testing

### Recommended Tests
- Penetration testing annually
- Dependency vulnerability scanning monthly
- Security code review quarterly
- MFA flow testing
- Rate limiting testing
- Session timeout testing
- CSRF token validation
- Security headers validation

## Contact
For security concerns or questions, contact the security team or create an issue in the repository.
