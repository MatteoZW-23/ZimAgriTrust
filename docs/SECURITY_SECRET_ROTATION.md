# Secret Rotation Guide

## Overview

This document outlines the procedures for rotating secrets in the ZimAgriTrust platform to maintain security hygiene and minimize the impact of potential secret compromises.

## Secrets Requiring Rotation

### High Priority (Rotate Quarterly)
- `SECRET_KEY` - JWT signing key for access tokens
- `REFRESH_SECRET_KEY` - JWT signing key for refresh tokens
- `SUPER_ADMIN_SECRET_KEY` - Super-admin authentication
- `TRANSACTION_SIGNING_KEY` - Financial transaction signing
- `AUDIT_CHAIN_KEY` - Audit log integrity

### Medium Priority (Rotate Semi-Annually)
- `PIN_PEPPER` - PIN hashing pepper
- `WHATSAPP_WEBHOOK_SECRET` - WhatsApp webhook verification
- `ECOCASH_WEBHOOK_SECRET` - EcoCash payment webhooks
- `ONEMONEY_WEBHOOK_SECRET` - OneMoney payment webhooks
- `ZIPIT_WEBHOOK_SECRET` - ZIPIT payment webhooks

### Low Priority (Rotate Annually)
- `WHATSAPP_API_KEY` - WhatsApp Business API
- `SENDGRID_API_KEY` - Email service
- `SMS_API_KEY` - SMS service provider
- `STRIPE_SECRET_KEY` - Stripe payments (if used)

## Rotation Procedure

### 1. Preparation

**Generate new secrets:**
```bash
# Generate secure random secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Backup current secrets:**
```bash
# Export current environment variables to backup file
env | grep -E "(SECRET_KEY|WEBHOOK_SECRET|API_KEY)" > secrets_backup_$(date +%Y%m%d).txt
```

### 2. Rotation Steps

#### JWT Secrets (SECRET_KEY, REFRESH_SECRET_KEY)

**Step 1: Add new secret alongside old**
```bash
# In .env file, add:
SECRET_KEY_NEW=<new_secret>
REFRESH_SECRET_KEY_NEW=<new_secret>
```

**Step 2: Update application to support dual keys**
- Modify `config.py` to check for new keys
- Update token generation to use new keys
- Keep old keys for verification of existing tokens

**Step 3: Wait for token expiry**
- Access tokens expire in 60 minutes
- Refresh tokens expire in 7 days
- Wait 7 days for all existing tokens to expire

**Step 4: Remove old keys**
```bash
# Replace old keys with new ones
SECRET_KEY=<new_secret>
REFRESH_SECRET_KEY=<new_secret>
# Remove SECRET_KEY_NEW and REFRESH_SECRET_KEY_NEW
```

#### Webhook Secrets

**Step 1: Update provider configuration**
- Update secret in provider dashboard (EcoCash, OneMoney, etc.)
- Update `WHATSAPP_WEBHOOK_SECRET` in `.env`

**Step 2: Update application configuration**
```bash
# In .env file
WHATSAPP_WEBHOOK_SECRET=<new_secret>
```

**Step 3: Restart services**
```bash
docker-compose restart backend whatsapp-service
```

#### Transaction Signing Key

**Step 1: Generate new key**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Step 2: Update configuration**
```bash
# In .env file
TRANSACTION_SIGNING_KEY=<new_key>
```

**Step 3: Restart services**
```bash
docker-compose restart backend celery-worker
```

**Note:** Old transactions remain valid; only new transactions use the new key.

### 3. Verification

**Test authentication:**
```bash
# Test login flow
curl -X POST https://api.zimagritrust.co.zw/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+263123456789","password":"test"}'
```

**Test webhooks:**
```bash
# Send test webhook with new signature
curl -X POST https://api.zimagritrust.co.zw/api/v1/payments/ecocash/webhook \
  -H "X-EcoCash-Signature: <new_signature>" \
  -d '{"test":true}'
```

**Test transactions:**
```bash
# Create test transaction
curl -X POST https://api.zimagritrust.co.zw/api/v1/wallet/top-up \
  -H "Authorization: Bearer <token>" \
  -d '{"amount":10.0,"currency":"USD"}'
```

### 4. Rollback Plan

If issues occur after rotation:

**Immediate rollback:**
```bash
# Restore from backup
cp secrets_backup_YYYYMMDD.txt .env
docker-compose restart
```

**Partial rollback:**
- Keep new secret for new operations
- Revert to old secret for verification only
- Monitor logs for authentication failures

### 5. Documentation

**Update documentation:**
- Record rotation date in this document
- Update any external provider dashboards
- Notify team of rotation completion

**Audit trail:**
```bash
# Log rotation event
echo "$(date): Rotated SECRET_KEY, REFRESH_SECRET_KEY" >> /var/log/agritrust/secret_rotations.log
```

## Automation

### Scheduled Rotation Script

Create `scripts/rotate_secrets.sh`:

```bash
#!/bin/bash
# Secret rotation automation script

SECRETS=(
  "SECRET_KEY"
  "REFRESH_SECRET_KEY"
  "WHATSAPP_WEBHOOK_SECRET"
)

for secret in "${SECRETS[@]}"; do
  echo "Rotating $secret..."
  NEW_VALUE=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  
  # Backup current value
  echo "${secret}_OLD=${!secret}" >> secrets_backup_$(date +%Y%m%d).txt
  
  # Set new value
  export $secret=$NEW_VALUE
  
  echo "Rotated $secret successfully"
done

echo "Secret rotation complete. Restart services."
```

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
name: Secret Rotation Check
on:
  schedule:
    - cron: '0 0 1 */3 *'  # Quarterly
  workflow_dispatch:

jobs:
  check-secret-age:
    runs-on: ubuntu-latest
    steps:
      - name: Check secret age
        run: |
          # Check if secrets are older than 90 days
          # Alert if rotation is needed
```

## Emergency Rotation

If a secret is compromised:

1. **Immediate action:**
   - Rotate all secrets immediately
   - Revoke all active sessions
   - Force password reset for all users

2. **Investigation:**
   - Review audit logs for unauthorized access
   - Check transaction logs for fraudulent activity
   - Identify time window of compromise

3. **Communication:**
   - Notify security team
   - Notify users of potential impact
   - Document incident

## Best Practices

1. **Never commit secrets to version control**
2. **Use environment-specific secrets** (dev, staging, prod)
3. **Rotate secrets before deployment** to new environments
4. **Document all rotations** with timestamps
5. **Test rotation in staging** before production
6. **Use secret management tools** (HashiCorp Vault, AWS Secrets Manager) for production
7. **Implement secret scanning** in CI/CD pipeline
8. **Monitor for secret leaks** in logs and error messages

## Contact

For questions or issues with secret rotation:
- Security Team: security@zimagritrust.co.zw
- DevOps Team: devops@zimagritrust.co.zw
- On-call: +263-XXX-XXX-XXXX

---

**Last Updated:** 2026-05-27
**Next Scheduled Rotation:** 2026-08-27
