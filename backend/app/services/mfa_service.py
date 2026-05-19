"""
Multi-Factor Authentication Service for ZimAgriTrust
Supports TOTP (Authenticator App) and backup codes.
MFA Required: SUPER_ADMIN, SYSTEM_ADMIN, FINANCE_ADMIN, REGIONAL_ADMIN
MFA Optional: SUPPORT_ADMIN, BRANCH_ADMIN, STAFF
"""
import hashlib
import hmac
import io
import secrets
import uuid
from base64 import b32encode
from datetime import datetime, timezone
from typing import Optional, Tuple

import pyotp
import qrcode
import qrcode.image.svg
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.security_enhanced import (
    MFAConfiguration,
    MFAAttempt,
    MFAMethod,
    MFAStatus,
    SecurityAuditLog,
    AuditLogAction,
)
from app.models.user import User, UserRole


# Roles that MUST have MFA enabled before accessing the system
MFA_REQUIRED_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.SYSTEM_ADMIN,
    UserRole.FINANCE_ADMIN,
    UserRole.REGIONAL_ADMIN,
    UserRole.REGIONAL_MANAGER,
}

# Roles that CAN optionally enable MFA
MFA_OPTIONAL_ROLES = {
    UserRole.SUPPORT_ADMIN,
    UserRole.BRANCH_ADMIN,
    UserRole.STAFF,
}

BACKUP_CODES_COUNT = 10
TOTP_ISSUER = "ZimAgriTrust"
TOTP_INTERVAL = 30  # seconds


class MFAService:
    """Multi-Factor Authentication service using TOTP and backup codes"""

    @staticmethod
    def is_mfa_required(user: User) -> bool:
        """Check if MFA is mandatory for this user's role"""
        return user.role in MFA_REQUIRED_ROLES

    @staticmethod
    def is_mfa_allowed(user: User) -> bool:
        """Check if MFA is available (required or optional) for this user's role"""
        return user.role in MFA_REQUIRED_ROLES or user.role in MFA_OPTIONAL_ROLES

    @staticmethod
    def get_mfa_config(db: Session, user_id: uuid.UUID) -> Optional[MFAConfiguration]:
        """Get user's MFA configuration"""
        return db.query(MFAConfiguration).filter(
            MFAConfiguration.user_id == user_id
        ).first()

    @staticmethod
    def is_mfa_enabled(db: Session, user_id: uuid.UUID) -> bool:
        """Check if user has MFA enabled and active"""
        config = MFAService.get_mfa_config(db, user_id)
        return config is not None and config.status == MFAStatus.ACTIVE

    @staticmethod
    def needs_mfa_setup(db: Session, user: User) -> bool:
        """Check if user needs to set up MFA before accessing system"""
        if not MFAService.is_mfa_required(user):
            return False
        return not MFAService.is_mfa_enabled(db, user.id)

    # ─── TOTP SETUP ─────────────────────────────────────────────────────────

    @staticmethod
    def begin_totp_setup(db: Session, user: User) -> dict:
        """
        Start TOTP setup process.
        Returns secret + QR code URI for the authenticator app.
        """
        if not MFAService.is_mfa_allowed(user):
            raise ValueError("MFA is not available for this role")

        # Generate TOTP secret
        secret = pyotp.random_base32(32)

        # Create or update MFA configuration
        config = MFAService.get_mfa_config(db, user.id)
        if not config:
            config = MFAConfiguration(
                user_id=user.id,
                totp_secret=secret,
                status=MFAStatus.SETUP_IN_PROGRESS,
            )
            db.add(config)
        else:
            config.totp_secret = secret
            config.status = MFAStatus.SETUP_IN_PROGRESS

        db.commit()

        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL)
        account_name = user.email or user.phone_number
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=TOTP_ISSUER,
        )

        # Generate QR code as base64 SVG
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        import base64
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_base64": f"data:image/png;base64,{qr_base64}",
            "issuer": TOTP_ISSUER,
            "account": account_name,
        }

    @staticmethod
    def confirm_totp_setup(
        db: Session, user: User, totp_code: str
    ) -> Tuple[bool, Optional[list]]:
        """
        Confirm TOTP setup by verifying the first code.
        Returns (success, backup_codes) — backup_codes only on success.
        """
        config = MFAService.get_mfa_config(db, user.id)
        if not config or not config.totp_secret:
            return False, None

        if config.status == MFAStatus.ACTIVE:
            return False, None  # Already set up

        # Verify the TOTP code
        totp = pyotp.TOTP(config.totp_secret, interval=TOTP_INTERVAL)
        if not totp.verify(totp_code, valid_window=settings.TOTP_WINDOW):
            return False, None

        # Generate backup codes
        backup_codes_plain = MFAService._generate_backup_codes()
        backup_codes_hashed = [
            get_password_hash(code) for code in backup_codes_plain
        ]

        # Activate MFA
        config.status = MFAStatus.ACTIVE
        config.totp_backup_codes = backup_codes_hashed
        config.enabled_at = datetime.now(timezone.utc)

        # Update user model
        user.mfa_enabled = True
        user.mfa_secret = config.totp_secret

        # Audit log
        audit = SecurityAuditLog(
            action=AuditLogAction.MFA_ENABLE,
            user_id=user.id,
            actor_id=user.id,
            resource_type="mfa",
            details={"method": "totp"},
            status="success",
        )
        db.add(audit)
        db.commit()

        return True, backup_codes_plain

    # ─── TOTP VERIFICATION ──────────────────────────────────────────────────

    @staticmethod
    def verify_totp(
        db: Session,
        user: User,
        code: str,
        ip_address: str = None,
    ) -> bool:
        """Verify a TOTP code from the authenticator app"""
        config = MFAService.get_mfa_config(db, user.id)
        if not config or config.status != MFAStatus.ACTIVE or not config.totp_secret:
            return False

        totp = pyotp.TOTP(config.totp_secret, interval=TOTP_INTERVAL)
        is_valid = totp.verify(code, valid_window=settings.TOTP_WINDOW)

        # Record attempt
        attempt = MFAAttempt(
            user_id=user.id,
            method=MFAMethod.TOTP,
            success=is_valid,
            ip_address=ip_address,
        )
        db.add(attempt)
        db.commit()

        return is_valid

    # ─── BACKUP CODES ────────────────────────────────────────────────────────

    @staticmethod
    def verify_backup_code(
        db: Session,
        user: User,
        code: str,
        ip_address: str = None,
    ) -> bool:
        """Verify and consume a backup code (single-use)"""
        config = MFAService.get_mfa_config(db, user.id)
        if not config or not config.totp_backup_codes:
            return False

        # Check each backup code
        for i, hashed_code in enumerate(config.totp_backup_codes):
            if verify_password(code, hashed_code):
                # Remove used code
                remaining = list(config.totp_backup_codes)
                remaining.pop(i)
                config.totp_backup_codes = remaining
                db.commit()

                # Record attempt
                attempt = MFAAttempt(
                    user_id=user.id,
                    method=MFAMethod.TOTP,
                    success=True,
                    ip_address=ip_address,
                )
                db.add(attempt)
                db.commit()

                return True

        # Record failed attempt
        attempt = MFAAttempt(
            user_id=user.id,
            method=MFAMethod.TOTP,
            success=False,
            ip_address=ip_address,
        )
        db.add(attempt)
        db.commit()

        return False

    @staticmethod
    def regenerate_backup_codes(db: Session, user: User) -> Optional[list]:
        """Regenerate backup codes (invalidates old ones)"""
        config = MFAService.get_mfa_config(db, user.id)
        if not config or config.status != MFAStatus.ACTIVE:
            return None

        backup_codes_plain = MFAService._generate_backup_codes()
        backup_codes_hashed = [
            get_password_hash(code) for code in backup_codes_plain
        ]
        config.totp_backup_codes = backup_codes_hashed
        db.commit()

        return backup_codes_plain

    # ─── DISABLE MFA ─────────────────────────────────────────────────────────

    @staticmethod
    def disable_mfa(
        db: Session,
        user: User,
        actor: User,
        reason: str = "user_request",
    ) -> bool:
        """
        Disable MFA for a user.
        Only allowed if MFA is optional for the role, or if done by a super admin.
        """
        if MFAService.is_mfa_required(user):
            if actor.role not in {UserRole.SUPER_ADMIN, UserRole.ADMIN}:
                raise ValueError("Cannot disable MFA for this role — it is mandatory")

        config = MFAService.get_mfa_config(db, user.id)
        if not config:
            return False

        config.status = MFAStatus.DISABLED
        config.totp_secret = None
        config.totp_backup_codes = None
        config.yubikey_public_id = None
        config.webauthn_credential_id = None

        user.mfa_enabled = False
        user.mfa_secret = None

        # Audit log
        audit = SecurityAuditLog(
            action=AuditLogAction.MFA_DISABLE,
            user_id=user.id,
            actor_id=actor.id,
            resource_type="mfa",
            details={"reason": reason, "disabled_by": str(actor.id)},
            status="success",
        )
        db.add(audit)
        db.commit()

        return True

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_backup_codes(count: int = BACKUP_CODES_COUNT) -> list:
        """Generate human-readable backup codes (8 chars, alphanumeric)"""
        codes = []
        for _ in range(count):
            # Format: XXXX-XXXX (easy to read/type)
            part1 = secrets.token_hex(2).upper()
            part2 = secrets.token_hex(2).upper()
            codes.append(f"{part1}-{part2}")
        return codes

    @staticmethod
    def get_remaining_backup_codes_count(db: Session, user_id: uuid.UUID) -> int:
        """Get count of remaining backup codes"""
        config = MFAService.get_mfa_config(db, user_id)
        if not config or not config.totp_backup_codes:
            return 0
        return len(config.totp_backup_codes)
