from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.auth import Login2FA, Token, UserLogin
from app.services.portal_auth_service import (
    ADMIN_PORTAL_ROLES,
    AGENT_PORTAL_ROLES,
    DRIVER_ROLES,
    PUBLIC_APP_ROLES,
    begin_mfa_login,
    complete_mfa_login,
    login_with_pin,
)

_DRIVER_OTP_PREFIX = "driver_otp:"
_DRIVER_OTP_TTL = 600  # 10 minutes


class DriverOtpRequest(BaseModel):
    phone_number: str


class DriverOtpVerify(BaseModel):
    phone_number: str
    otp: str

app_auth_router = APIRouter()
driver_auth_router = APIRouter()
admin_auth_router = APIRouter()
agent_auth_router = APIRouter()


def _enforce_portal_host(request: Request, expected: str) -> None:
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(":")[0].lower()
    expected_host = (expected or "").strip().lower()
    if expected_host and host and host != expected_host:
        raise HTTPException(status_code=403, detail=f"Portal host mismatch. Use {expected_host}")


# Global OPTIONS handler for driver auth router
@driver_auth_router.options("/{path:path}")
async def driver_auth_options(path: str):
    """Handle CORS preflight for all driver auth routes"""
    return {"status": "ok"}


@app_auth_router.post("/login", response_model=Token)
async def login_app_user(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    """PIN login for the unified Farmer/Buyer app and web portal."""
    return await login_with_pin(
        db=db,
        request=request,
        response=response,
        phone_number=payload.phone_number,
        pin=payload.password,
        allowed_roles=PUBLIC_APP_ROLES,
        portal_name="app",
    )


@driver_auth_router.options("/request-otp")
async def driver_request_otp_options(request: Request):
    """Handle CORS preflight for request-otp"""
    return {"status": "ok"}


@driver_auth_router.post("/request-otp", summary="Request OTP for driver self-registration")
async def driver_request_otp(
    payload: DriverOtpRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Send a 6-digit OTP to the driver's phone for registration verification."""
    from app.services.cache_service import cache_service
    import logging
    _log = logging.getLogger(__name__)

    otp = f"{secrets.randbelow(1_000_000):06d}"
    await cache_service.set(f"{_DRIVER_OTP_PREFIX}{payload.phone_number}", otp, expire=_DRIVER_OTP_TTL)

    from app.services.whatsapp_service import WhatsAppService
    message = f"🚚 *ZimAgriTrust Driver Verification*\n\nYour OTP code is: {otp}\n\nValid for 10 minutes. Do not share this code with anyone."
    try:
        await WhatsAppService.send_whatsapp_message(payload.phone_number, message)
    except Exception as e:
        _log.warning("Failed to send WhatsApp OTP: %s", e)

    from app.services.sms_service import send_otp as sms_send_otp
    try:
        sms_send_otp(payload.phone_number, otp)
    except Exception as e:
        _log.warning("Failed to send SMS OTP: %s", e)

    _log.info("Driver OTP dispatched for %s", payload.phone_number)
    return {"status": "sent", "message": "OTP sent to your phone number"}


@driver_auth_router.post("/verify-otp", summary="Verify OTP and get temp registration token")
async def driver_verify_otp(
    payload: DriverOtpVerify,
    db: Session = Depends(get_db),
) -> dict:
    """Verify OTP; returns a short-lived temp_token for the registration form submission."""
    from app.services.cache_service import cache_service
    otp_key = f"{_DRIVER_OTP_PREFIX}{payload.phone_number}"
    stored_otp = await cache_service.get(otp_key)
    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP found for this number. Request a new one.")
    if stored_otp != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
    await cache_service.delete(otp_key)
    # Issue a short-lived temp token (15 min) scoped to registration only
    now = datetime.now(timezone.utc)
    temp_token = jwt.encode(
        {
            "sub":   payload.phone_number,
            "scope": "driver_registration",
            "exp":   int((now + timedelta(minutes=15)).timestamp()),
            "iat":   int(now.timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return {"temp_token": temp_token, "phone_number": payload.phone_number}


@driver_auth_router.post("/login", response_model=Token)
async def login_driver(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    """PIN login for the driver-only mobile app."""
    return await login_with_pin(
        db=db,
        request=request,
        response=response,
        phone_number=payload.phone_number,
        pin=payload.password,
        allowed_roles=DRIVER_ROLES,
        portal_name="driver",
    )


@admin_auth_router.post("/login")
async def begin_admin_login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Password + MFA login for Admin/HQ web portal only."""
    _enforce_portal_host(request, getattr(settings, "ADMIN_PORTAL_HOST", ""))
    return await begin_mfa_login(
        db=db,
        request=request,
        phone_number=payload.phone_number,
        password=payload.password,
        allowed_roles=ADMIN_PORTAL_ROLES,
        portal_name="admin",
    )


@admin_auth_router.post("/verify-mfa", response_model=Token)
async def verify_admin_mfa(
    payload: Login2FA,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    _enforce_portal_host(request, getattr(settings, "ADMIN_PORTAL_HOST", ""))
    return await complete_mfa_login(
        db=db,
        request=request,
        response=response,
        phone_number=payload.phone_number,
        otp=payload.otp,
        allowed_roles=ADMIN_PORTAL_ROLES,
        portal_name="admin",
    )


@agent_auth_router.post("/login")
async def begin_agent_login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Password + MFA login for Agent web portal only."""
    _enforce_portal_host(request, getattr(settings, "AGENT_PORTAL_HOST", ""))
    return await begin_mfa_login(
        db=db,
        request=request,
        phone_number=payload.phone_number,
        password=payload.password,
        allowed_roles=AGENT_PORTAL_ROLES,
        portal_name="agent",
    )


@agent_auth_router.post("/verify-mfa", response_model=Token)
async def verify_agent_mfa(
    payload: Login2FA,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    return await complete_mfa_login(
        db=db,
        request=request,
        response=response,
        phone_number=payload.phone_number,
        otp=payload.otp,
        allowed_roles=AGENT_PORTAL_ROLES,
        portal_name="agent",
    )
