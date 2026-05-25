"""
Super-admin authentication and authorization.

Three-step login:
  1) POST /super-admin/login          — username + password → pre-MFA token
  2) POST /super-admin/verify-mfa     — pre-MFA token + TOTP/YubiKey → access token
  3) Use Bearer access token (30-min) for /super-admin/* endpoints

Hardware MFA: TOTP (Authenticator app) is enforced by default. A YubiKey OTP
public-id may be configured per-account for dual-factor enrolment.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.super_admin_security import (
    create_super_admin_pre_mfa_token,
    create_super_admin_token,
    decode_super_admin_token,
    is_valid_super_admin_token,
    super_admin_ip_allowed,
    SUPER_ADMIN_PRE_MFA_TOKEN_TYPE,
    verify_totp,
    verify_yubikey_otp,
)
from app.models.security import SuperAdmin

logger = logging.getLogger(__name__)


MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 30


# ---------------------------------------------------------------------------
# Account lookup helpers
# ---------------------------------------------------------------------------

def get_super_admin(db: Session, super_admin_id: int) -> Optional[SuperAdmin]:
    return db.query(SuperAdmin).filter(SuperAdmin.id == super_admin_id).first()


def get_super_admin_by_username(db: Session, username: str) -> Optional[SuperAdmin]:
    return db.query(SuperAdmin).filter(SuperAdmin.username == username).first()


# ---------------------------------------------------------------------------
# IP enforcement
# ---------------------------------------------------------------------------

def enforce_ip(request: Request, account: Optional[SuperAdmin] = None) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    account_wl = list(account.ip_whitelist or []) if (account and account.ip_whitelist) else []
    if not super_admin_ip_allowed(client_ip, account_wl):
        logger.warning("SUPER_ADMIN | IP blocked | ip=%s | account=%s", client_ip, account.id if account else "?")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address",
        )
    return client_ip


# ---------------------------------------------------------------------------
# Login flow
# ---------------------------------------------------------------------------

def login_step_1(
    db: Session,
    *,
    request: Request,
    username: str,
    password: str,
) -> dict:
    """Verify password, return pre-MFA token."""
    account = get_super_admin_by_username(db, username)
    if not account or not account.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    enforce_ip(request, account)

    if account.locked_until and account.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked until {account.locked_until.isoformat()}",
        )

    if not verify_password(password, account.password_hash):
        account.failed_login_count = (account.failed_login_count or 0) + 1
        if account.failed_login_count >= MAX_FAILED_LOGINS:
            account.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    pre_mfa = create_super_admin_pre_mfa_token(account.id)
    return {
        "status": "MFA_REQUIRED",
        "pre_mfa_token": pre_mfa,
        "expires_in": 300,
        "mfa_methods": _available_mfa_methods(account),
    }


def verify_mfa(
    db: Session,
    *,
    request: Request,
    pre_mfa_token: str,
    mfa_code: str,
    method: str = "totp",
) -> dict:
    """Verify TOTP or YubiKey OTP. On success, issue full super-admin access token."""
    try:
        payload = decode_super_admin_token(pre_mfa_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Pre-MFA token invalid") from exc

    if payload.get("type") != SUPER_ADMIN_PRE_MFA_TOKEN_TYPE:
        raise HTTPException(status_code=401, detail="Wrong token type")

    account = get_super_admin(db, int(payload["sub"]))
    if not account or not account.is_active:
        raise HTTPException(status_code=401, detail="Account not active")

    client_ip = enforce_ip(request, account)

    ok = False
    if method == "totp":
        ok = bool(account.hardware_mfa_secret) and verify_totp(account.hardware_mfa_secret, mfa_code)
    elif method == "yubikey":
        ok = bool(account.yubikey_public_id) and verify_yubikey_otp(mfa_code, account.yubikey_public_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported MFA method: {method}")

    if not ok:
        account.failed_login_count = (account.failed_login_count or 0) + 1
        if account.failed_login_count >= MAX_FAILED_LOGINS:
            account.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        db.commit()
        raise HTTPException(status_code=401, detail="MFA verification failed")

    account.failed_login_count = 0
    account.locked_until = None
    account.last_login_at = datetime.now(timezone.utc)
    account.last_login_ip = client_ip
    db.commit()

    access_token = create_super_admin_token(account.id, mfa_verified=True)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.SUPER_ADMIN_TOKEN_EXPIRE_MINUTES * 60,
        "super_admin": {
            "id": account.id,
            "username": account.username,
            "email": account.email,
        },
    }


def _available_mfa_methods(account: SuperAdmin) -> list[str]:
    methods: list[str] = []
    if account.hardware_mfa_secret:
        methods.append("totp")
    if account.yubikey_public_id:
        methods.append("yubikey")
    return methods or ["totp"]


# ---------------------------------------------------------------------------
# Token validation (used by the FastAPI dependency)
# ---------------------------------------------------------------------------

def authenticate_super_admin(token: str, db: Session, request: Optional[Request] = None) -> SuperAdmin:
    payload = is_valid_super_admin_token(token, require_mfa=True)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired super-admin token")
    account = get_super_admin(db, int(payload["sub"]))
    if not account or not account.is_active:
        raise HTTPException(status_code=401, detail="Super admin account not active")
    if request is not None:
        enforce_ip(request, account)
    return account


# ---------------------------------------------------------------------------
# Account creation (seed-only path; never exposed via normal flow)
# ---------------------------------------------------------------------------

def seed_super_admin(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    hardware_mfa_secret: Optional[str] = None,
    yubikey_public_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    ip_whitelist: Optional[list[str]] = None,
    created_by: Optional[int] = None,
) -> SuperAdmin:
    if get_super_admin_by_username(db, username):
        raise ValueError(f"super admin '{username}' already exists")
    account = SuperAdmin(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        hardware_mfa_secret=hardware_mfa_secret,
        yubikey_public_id=yubikey_public_id,
        phone_number=phone_number,
        ip_whitelist=ip_whitelist or [],
        is_active=True,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
