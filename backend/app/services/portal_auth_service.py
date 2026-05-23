from __future__ import annotations

import math
import random
import secrets
from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import Token, UserResponse
from app.services.auth_service import authenticate_user, build_phone_lookup_candidates
from app.services.cache_service import cache_service
from app.services.mfa_service import MFAService
from app.services.notification_service import NotificationService
from app.services.rate_limit_service import (
    clear_login_failures,
    enforce_rate_limit,
    ensure_login_not_locked,
    record_login_failure,
)
from app.services.session_service import create_session

OTP_TTL_SECONDS = 300

# ── Role sets for portal gate checks ─────────────────────────────────────────
PUBLIC_APP_ROLES = {UserRole.FARMER, UserRole.BUYER}
DRIVER_ROLES = {UserRole.DRIVER}
SUPPLIER_ROLES = {UserRole.SUPPLIER}
STAFF_ROLES = {UserRole.STAFF}
AGENT_PORTAL_ROLES = {UserRole.AGENT}
ADMIN_PORTAL_ROLES = {
    UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN,
    UserRole.FINANCE_ADMIN, UserRole.REGIONAL_ADMIN, UserRole.REGIONAL_MANAGER,
    UserRole.SUPPORT_ADMIN, UserRole.BRANCH_ADMIN,
}
PUBLIC_MOBILE_ROLES = PUBLIC_APP_ROLES | DRIVER_ROLES

# ── Portal routing by role ───────────────────────────────────────────────────
ROLE_PORTALS = {
    UserRole.FARMER: ("app", "/app"),
    UserRole.BUYER: ("app", "/app"),
    UserRole.DRIVER: ("driver", "/driver"),
    UserRole.STAFF: ("admin", "/admin"),
    UserRole.AGENT: ("agent", "/agent"),
    UserRole.SUPPLIER: ("supplier", "/supplier"),
    UserRole.BRANCH_ADMIN: ("admin", "/admin"),
    UserRole.SUPPORT_ADMIN: ("admin", "/admin"),
    UserRole.REGIONAL_ADMIN: ("admin", "/admin"),
    UserRole.REGIONAL_MANAGER: ("admin", "/admin"),
    UserRole.FINANCE_ADMIN: ("admin", "/admin"),
    UserRole.SYSTEM_ADMIN: ("admin", "/admin"),
    UserRole.ADMIN: ("admin", "/admin"),
    UserRole.SUPER_ADMIN: ("admin", "/admin"),
}

# ── Role-based token expiry (minutes) ────────────────────────────────────────
ACCESS_TOKEN_EXPIRY_BY_ROLE = {
    UserRole.SUPER_ADMIN: 15, UserRole.ADMIN: 15,
    UserRole.SYSTEM_ADMIN: 30, UserRole.FINANCE_ADMIN: 30,
    UserRole.REGIONAL_ADMIN: 30, UserRole.REGIONAL_MANAGER: 30,
    UserRole.SUPPORT_ADMIN: 60, UserRole.BRANCH_ADMIN: 60,
    UserRole.SUPPLIER: 60, UserRole.STAFF: 60,
    UserRole.AGENT: 480,  # 8 hours
    UserRole.DRIVER: 60,
    UserRole.FARMER: 60, UserRole.BUYER: 60,
}

REFRESH_TOKEN_EXPIRY_DAYS_BY_ROLE = {
    UserRole.SUPER_ADMIN: 7, UserRole.ADMIN: 7,
    UserRole.SYSTEM_ADMIN: 7, UserRole.FINANCE_ADMIN: 7,
    UserRole.REGIONAL_ADMIN: 7, UserRole.REGIONAL_MANAGER: 7,
    UserRole.SUPPORT_ADMIN: 14, UserRole.BRANCH_ADMIN: 14,
    UserRole.SUPPLIER: 30, UserRole.STAFF: 14,
    UserRole.AGENT: 30,
    UserRole.DRIVER: 30,
    UserRole.FARMER: 30, UserRole.BUYER: 30,
}


def portal_for_role(role: UserRole) -> tuple[str, str]:
    return ROLE_PORTALS.get(role, ("public", "/"))


def ensure_role(user: User, allowed_roles: Iterable[UserRole], portal_name: str) -> None:
    allowed = set(allowed_roles)
    if user.role not in allowed:
        expected_portal, expected_path = portal_for_role(user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"This account cannot access the {portal_name} portal.",
                "role": user.role.value,
                "expected_portal": expected_portal,
                "expected_path": expected_path,
            },
        )


def ensure_active_user(user: User) -> None:
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"ACCOUNT_PENDING: Your profile status is '{user.status.value}'. Access restricted until approval.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")


async def set_otp(key: str, otp: str) -> None:
    await cache_service.set(f"otp:{key}", otp, expire=OTP_TTL_SECONDS)


async def get_otp(key: str) -> str | None:
    return await cache_service.get(f"otp:{key}")


async def clear_otp(key: str) -> None:
    await cache_service.delete(f"otp:{key}")


def _cookie_secure() -> bool:
    return bool(settings.FORCE_HTTPS)


def _refresh_days() -> int:
    return max(1, math.ceil(settings.REFRESH_TOKEN_EXPIRE_MINUTES / 1440))


async def issue_session_token(
    *,
    db: Session,
    user: User,
    request: Request,
    response: Response,
    must_change_password: bool = False,
    mfa_required: bool = False,
) -> Token:
    # Role-based token expiry
    access_minutes = ACCESS_TOKEN_EXPIRY_BY_ROLE.get(user.role, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_days = REFRESH_TOKEN_EXPIRY_DAYS_BY_ROLE.get(user.role, _refresh_days())

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    await create_session(
        db=db,
        user_id=user.id,
        access_token_jti=access_payload.get("jti"),
        refresh_token_jti=refresh_payload.get("jti"),
        request_headers=dict(request.headers),
        ip_address=request.client.host if request.client else "unknown",
        access_expiry_minutes=access_minutes,
        refresh_expiry_days=refresh_days,
    )

    cookie_secure = _cookie_secure()
    access_max_age = access_minutes * 60
    refresh_max_age = refresh_days * 24 * 3600
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=access_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=refresh_max_age,
    )

    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=cookie_secure,
        samesite="lax",
        max_age=refresh_max_age,
    )
    response.headers["X-CSRF-Token"] = csrf_token

    portal, portal_path = portal_for_role(user.role)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        must_change_password=must_change_password,
        portal=portal,
        portal_path=portal_path,
        allowed_portals=[portal],
    )


async def login_with_pin(
    *,
    db: Session,
    request: Request,
    response: Response,
    phone_number: str,
    pin: str,
    allowed_roles: set[UserRole],
    portal_name: str,
) -> Token:
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:{portal_name}:pin:ip:{client_host}",
        limit=20,
        window_seconds=300,
        detail="Too many login attempts from this origin",
    )
    await ensure_login_not_locked(phone_number)

    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user or not user.ussd_pin_hash or not verify_password(pin, user.ussd_pin_hash):
        failures = await record_login_failure(phone_number)
        if failures >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone or PIN")

    ensure_role(user, allowed_roles, portal_name)
    ensure_active_user(user)
    await clear_login_failures(phone_number)
    return await issue_session_token(db=db, user=user, request=request, response=response)


async def begin_mfa_login(
    *,
    db: Session,
    request: Request,
    phone_number: str,
    password: str,
    allowed_roles: set[UserRole],
    portal_name: str,
) -> dict[str, Any]:
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:{portal_name}:password:ip:{client_host}",
        limit=10,
        window_seconds=300,
        detail="Too many privileged login attempts from this origin",
    )
    await ensure_login_not_locked(phone_number)

    user = authenticate_user(db, phone_number, password)
    if not user:
        failures = await record_login_failure(phone_number)
        if failures >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone or password")

    ensure_role(user, allowed_roles, portal_name)
    ensure_active_user(user)
# Check if TOTP MFA is required and not set up
    if MFAService.needs_mfa_setup(db, user):
        return {
            "status": "MFA_SETUP_REQUIRED",
            "message": "Multi-factor authentication is required for your role. Please set up TOTP authenticator app.",
            "phone": user.phone_number,
            "portal": portal_name,
            "mfa_required": True,
        }

    # Check if TOTP MFA is enabled
    mfa_enabled = MFAService.is_mfa_enabled(db, user.id)
    if mfa_enabled:
        return {
            "status": "TOTP_REQUIRED",
            "message": "Enter your TOTP code from your authenticator app.",
            "phone": user.phone_number,
            "portal": portal_name,
            "mfa_method": "totp",
        }

    # Send OTP via SMS and WhatsApp
    otp = str(random.randint(100000, 999999))
    await set_otp(f"{portal_name}:mfa:{phone_number}", otp)
    await NotificationService.send_verification_code(user.phone_number, otp)

    return {
        "status": "MFA_REQUIRED",
        "message": "Verification code sent via SMS and WhatsApp.",
        "phone": user.phone_number,
        "portal": portal_name,
    }


async def complete_mfa_login(
    *,
    db: Session,
    request: Request,
    response: Response,
    phone_number: str,
    otp: str,
    portal_name: str,
    allowed_roles: set[UserRole],
) -> Token:
    cached_otp = await get_otp(f"{portal_name}:mfa:{phone_number}")
    if not cached_otp or otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    candidates = build_phone_lookup_candidates(phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    ensure_role(user, allowed_roles, portal_name)
    ensure_active_user(user)

    if not user.is_phone_verified:
        from datetime import datetime, timezone

        user.is_phone_verified = True
        user.phone_verified_at = datetime.now(timezone.utc)
        db.commit()

    await clear_login_failures(phone_number)
    await clear_otp(f"{portal_name}:mfa:{phone_number}")

    must_change = bool(user.must_change_password)
    return await issue_session_token(
        db=db,
        user=user,
        request=request,
        response=response,
        must_change_password=must_change,
    )
