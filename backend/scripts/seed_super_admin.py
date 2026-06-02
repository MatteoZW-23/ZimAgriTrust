#!/usr/bin/env python3
"""
Seed the first Super Admin for ZimAgriTrust.

This script creates the initial super admin account directly in the database.
Super admins should NEVER be created via normal API endpoints - only through
database seeding or by another super admin with co-approval.

Usage:
    python scripts/seed_super_admin.py

Environment variables:
    SUPER_ADMIN_USERNAME - Username for the super admin (required)
    SUPER_ADMIN_EMAIL - Email for the super admin (required)
    SUPER_ADMIN_PASSWORD - Password for the super admin (required)
    SUPER_ADMIN_PHONE - Phone number (optional, for OTP alerts)
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from getpass import getpass
import io
import base64
import pyotp
import qrcode
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.security import SuperAdmin
from app.services import super_admin_service
from app.core.super_admin_security import verify_totp

TOTP_ISSUER = "ZimAgriTrust"
TOTP_INTERVAL = 30


def setup_mfa_for_super_admin(db: Session, super_admin: SuperAdmin) -> str:
    """Set up MFA for a super admin and return the secret."""
    
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
    
    # Save QR code to file
    qr_filename = f"/tmp/mfa_qr_{super_admin.username}.png"
    img.save(qr_filename)
    
    print(f"\n{'='*60}")
    print("MFA SETUP - SCAN QR CODE")
    print(f"{'='*60}")
    print(f"\nQR Code saved to: {qr_filename}")
    print(f"\nQR Code URI: {provisioning_uri}")
    print(f"\nManual entry secret: {secret}")
    print(f"\n{'='*60}")
    
    # Store the secret in the database
    super_admin.hardware_mfa_secret = secret
    db.commit()
    
    return secret


def create_super_admin(
    db: Session,
    username: str,
    email: str,
    password: str,
    phone: str = None,
    ip_whitelist: list = None,
    setup_mfa: bool = True
) -> SuperAdmin:
    """Create a super admin account with optional MFA setup."""
    
    existing = db.query(SuperAdmin).filter(
        (SuperAdmin.username == username) | (SuperAdmin.email == email)
    ).first()
    if existing:
        print(f"Super admin with username '{username}' or email '{email}' already exists.")
        return existing

    super_admin = super_admin_service.seed_super_admin(
        db,
        username=username,
        email=email,
        password=password,
        phone_number=phone,
        ip_whitelist=ip_whitelist or [],
    )
    
    print(f"✓ Super admin created successfully!")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Phone: {phone or 'Not set'}")
    print(f"  ID: {super_admin.id}")
    
    # Set up MFA automatically
    if setup_mfa:
        secret = setup_mfa_for_super_admin(db, super_admin)
        print(f"\n⚠️  IMPORTANT: Save this TOTP secret securely!")
        print(f"   Secret: {secret}")
        print(f"   Scan the QR code above with your authenticator app")
        print(f"   (Google Authenticator, Authy, etc.)")
    
    return super_admin


def main():
    """Main entry point."""
    
    # Get credentials from environment or prompt
    username = os.getenv("SUPER_ADMIN_USERNAME")
    email = os.getenv("SUPER_ADMIN_EMAIL")
    password = os.getenv("SUPER_ADMIN_PASSWORD")
    phone = os.getenv("SUPER_ADMIN_PHONE")
    
    if not username:
        username = input("Enter super admin username: ").strip()
    
    if not email:
        email = input("Enter super admin email: ").strip()
    
    if not password:
        password = getpass("Enter super admin password: ").strip()
        confirm = getpass("Confirm password: ").strip()
        if password != confirm:
            print("Passwords do not match!")
            sys.exit(1)
    
    if not phone:
        phone = input("Enter phone number (optional, press Enter to skip): ").strip() or None
    
    # Validate inputs
    if not username or not email or not password:
        print("ERROR: Username, email, and password are required!")
        sys.exit(1)
    
    if len(password) < 12:
        print("WARNING: Password should be at least 12 characters for security.")
        proceed = input("Continue anyway? (yes/no): ").strip().lower()
        if proceed != "yes":
            sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        create_super_admin(db, username, email, password, phone)
    except Exception as e:
        print(f"ERROR: Failed to create super admin: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
