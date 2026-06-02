#!/usr/bin/env python3
"""
Set up MFA for an existing super admin user.

This script enables TOTP-based MFA for a super admin.
The QR code and secret will be displayed for setup.

Usage:
    python scripts/setup_mfa.py

Environment variables:
    SUPER_ADMIN_EMAIL - Email of the super admin to set up MFA for
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import io
import base64
import pyotp
import qrcode
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.security import SuperAdmin
from app.core.super_admin_security import verify_totp

TOTP_ISSUER = "ZimAgriTrust"
TOTP_INTERVAL = 30


def setup_mfa_for_super_admin(db: Session, email: str) -> dict:
    """Set up MFA for a super admin by email."""
    
    # Find the super admin
    super_admin = db.query(SuperAdmin).filter(SuperAdmin.email == email).first()
    if not super_admin:
        print(f"ERROR: Super admin with email '{email}' not found.")
        sys.exit(1)
    
    # Check if MFA is already enabled
    if super_admin.hardware_mfa_secret:
        print(f"MFA is already enabled for {email}")
        return {"status": "already_enabled"}
    
    # Generate TOTP secret
    secret = pyotp.random_base32(32)
    
    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL)
    account_name = super_admin.email or super_admin.phone_number
    provisioning_uri = totp.provisioning_uri(
        name=account_name,
        issuer_name=TOTP_ISSUER,
    )
    
    # Generate QR code as base64 PNG
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    print(f"Setting up MFA for {super_admin.username} ({email})...")
    print("\n" + "="*60)
    print("MFA SETUP INSTRUCTIONS")
    print("="*60)
    print(f"\n1. Scan this QR code with your authenticator app:")
    print(f"   (Google Authenticator, Authy, etc.)")
    print(f"\n   QR Code URI: {provisioning_uri}")
    print(f"\n2. Or enter this secret manually:")
    print(f"   Secret: {secret}")
    print(f"\n3. Enter a code from your authenticator app to confirm setup:")
    
    # Get the verification code from user
    while True:
        totp_code = input("\nEnter TOTP code (or 'quit' to cancel): ").strip()
        if totp_code.lower() == 'quit':
            print("MFA setup cancelled.")
            db.rollback()
            sys.exit(0)
        
        # Verify the code
        if verify_totp(secret, totp_code):
            # Store the secret in the database
            super_admin.hardware_mfa_secret = secret
            db.commit()
            
            print("\n✓ MFA enabled successfully!")
            print("\n" + "="*60)
            print("⚠️  IMPORTANT: Save your TOTP secret securely!")
            print(f"   Secret: {secret}")
            print("   If you lose your authenticator device, you will need")
            print("   this secret to regain access to your account.")
            print("\n" + "="*60)
            return {"status": "enabled", "secret": secret}
        else:
            print("Invalid code. Please try again.")


def main():
    """Main entry point."""
    
    # Get email from environment or prompt
    email = os.getenv("SUPER_ADMIN_EMAIL")
    if not email:
        email = input("Enter super admin email: ").strip()
    
    if not email:
        print("ERROR: Email is required!")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        setup_mfa_for_super_admin(db, email)
    except Exception as e:
        print(f"ERROR: Failed to set up MFA: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
