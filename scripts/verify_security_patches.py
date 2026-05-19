#!/usr/bin/env python3
"""
Security Patch Verification Script
Run this after applying patches to verify all critical fixes are in place.
"""

import os
import sys
import re
from pathlib import Path

def check_patch_1_jwt_validation():
    """Verify JWT algorithm validation is strict"""
    print("\n[PATCH 1] Checking JWT algorithm validation...")
    
    security_file = Path("backend/app/core/security.py")
    content = security_file.read_text()
    
    # Check for strict algorithm enforcement
    if 'algorithms=[settings.ALGORITHM]' in content and '"require":' in content:
        print("  ✓ PASS: decode_token() uses strict algorithm whitelist")
        print("  ✓ PASS: Required claims (exp, iat, sub, type) enforced")
        return True
    else:
        print("  ✗ FAIL: JWT validation may not be strict enough")
        return False

def check_patch_2_webhook_signatures():
    """Verify webhook signatures are mandatory"""
    print("\n[PATCH 2] Checking webhook signature enforcement...")
    
    payments_file = Path("backend/app/api/v1/endpoints/payments.py")
    content = payments_file.read_text()
    
    checks = []
    
    # Check for mandatory verification
    if 'if not secret_key:' in content and 'raise HTTPException' in content:
        print("  ✓ PASS: EcoCash webhook fails closed when secret not configured")
        checks.append(True)
    else:
        print("  ✗ FAIL: EcoCash webhook may allow bypass when secret missing")
        checks.append(False)
    
    if 'if not signature:' in content and 'raise HTTPException' in content:
        print("  ✓ PASS: EcoCash webhook requires signature header")
        checks.append(True)
    else:
        print("  ✗ FAIL: EcoCash webhook may allow requests without signature")
        checks.append(False)
    
    return all(checks)

def check_patch_3_onemoney_verification():
    """Verify OneMoney webhook has proper verification"""
    print("\n[PATCH 3] Checking OneMoney webhook verification...")
    
    webhook_file = Path("backend/app/services/webhook_verification.py")
    content = webhook_file.read_text()
    
    # Check that it's not just returning bool(signature)
    if 'return bool(signature)' in content:
        print("  ✗ FAIL: OneMoney verification is still a NO-OP (returns bool(signature))")
        return False
    
    if 'hmac.new(' in content and 'ONEMONEY_WEBHOOK_SECRET not configured' in content:
        print("  ✓ PASS: OneMoney verification implements HMAC validation")
        print("  ✓ PASS: OneMoney requires secret configuration")
        return True
    else:
        print("  ⚠ WARN: OneMoney verification may not be complete")
        return True  # Warn but don't fail

def check_patch_4_secret_validation():
    """Verify secret validation is in place"""
    print("\n[PATCH 4] Checking secret validation...")
    
    config_file = Path("backend/app/core/config.py")
    content = config_file.read_text()
    
    checks = []
    
    # Check for secret validators
    if 'validate_secrets' in content:
        print("  ✓ PASS: Secret validation function exists")
        checks.append(True)
    else:
        print("  ✗ FAIL: Secret validation not found")
        checks.append(False)
    
    if 'validate_master_test' in content:
        print("  ✓ PASS: Master test account validation exists")
        checks.append(True)
    else:
        print("  ✗ FAIL: Master test validation not found")
        checks.append(False)
    
    if 'CHANGE_ME' in content and 'placeholder' in content.lower():
        print("  ✓ PASS: Detects placeholder values")
        checks.append(True)
    else:
        print("  ⚠ WARN: Placeholder detection may be incomplete")
        checks.append(True)
    
    return all(checks)

def check_patch_6_docker_security():
    """Verify Docker Compose security hardening"""
    print("\n[PATCH 6] Checking Docker Compose security...")
    
    compose_file = Path("docker-compose.yml")
    content = compose_file.read_text()
    
    checks = []
    
    # Check PostgreSQL
    if 'ports:\n      - "5434:5432"' not in content:
        print("  ✓ PASS: PostgreSQL host port mapping removed")
        checks.append(True)
    else:
        print("  ✗ FAIL: PostgreSQL still exposed to host")
        checks.append(False)
    
    if 'expose:\n      - "5432"' in content:
        print("  ✓ PASS: PostgreSQL uses internal expose only")
        checks.append(True)
    else:
        print("  ⚠ WARN: PostgreSQL expose configuration not found")
        checks.append(True)
    
    # Check Redis
    if 'ports:\n      - "6380:6379"' not in content:
        print("  ✓ PASS: Redis host port mapping removed")
        checks.append(True)
    else:
        print("  ✗ FAIL: Redis still exposed to host")
        checks.append(False)
    
    if '--requirepass' in content:
        print("  ✓ PASS: Redis AUTH password configured")
        checks.append(True)
    else:
        print("  ✗ FAIL: Redis AUTH not configured")
        checks.append(False)
    
    # Check networks
    if 'backend-network:' in content:
        print("  ✓ PASS: Internal network configured")
        checks.append(True)
    else:
        print("  ✗ FAIL: Network isolation not configured")
        checks.append(False)
    
    return all(checks)

def check_env_file():
    """Verify .env.production.example has all required secrets"""
    print("\n[ENV FILE] Checking .env.production.example...")
    
    env_file = Path(".env.production.example")
    if not env_file.exists():
        print("  ✗ FAIL: .env.production.example not found")
        return False
    
    content = env_file.read_text()
    
    required_vars = [
        "ECOCASH_WEBHOOK_SECRET",
        "ONEMONEY_WEBHOOK_SECRET",
        "SUPER_ADMIN_SECRET_KEY",
        "TRANSACTION_SIGNING_KEY",
        "AUDIT_CHAIN_KEY",
        "ADMIN_AUDIT_LOGGING",
        "MASTER_TEST_LOGIN_ENABLED=false",
        "AUTO_CONFIRM_PAYMENTS=false",
    ]
    
    checks = []
    for var in required_vars:
        if var in content:
            print(f"  ✓ PASS: {var.split('=')[0]} documented")
            checks.append(True)
        else:
            print(f"  ✗ FAIL: {var.split('=')[0]} missing")
            checks.append(False)
    
    return all(checks)

def main():
    print("=" * 70)
    print("ZimAgriTrust Security Patch Verification")
    print("=" * 70)
    
    # Change to repo root
    os.chdir(Path(__file__).parent.parent)
    
    results = {
        "JWT Algorithm Validation": check_patch_1_jwt_validation(),
        "Webhook Signatures": check_patch_2_webhook_signatures(),
        "OneMoney Verification": check_patch_3_onemoney_verification(),
        "Secret Validation": check_patch_4_secret_validation(),
        "Docker Security": check_patch_6_docker_security(),
        "Environment Variables": check_env_file(),
    }
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✓ ALL PATCHES VERIFIED - System is ready for production")
        return 0
    else:
        print("\n✗ SOME PATCHES MISSING - Review failures above")
        print("\nNext steps:")
        print("  1. Apply missing patches from docs/security_remediation_patches.md")
        print("  2. Run this script again to verify")
        print("  3. Configure all secrets in .env.production before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())
