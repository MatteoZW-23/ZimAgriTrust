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

# ── In-memory OTP store (replace with Redis in production) ───────────────────
_driver_otp_store: dict[str, dict] = {}


class DriverOtpRequest(BaseModel):
    phone_number: str


class DriverOtpVerify(BaseModel):
    phone_number: str
    otp: str

app_auth_router = APIRouter()
driver_auth_router = APIRouter()
admin_auth_router = APIRouter()
agent_auth_router = APIRouter()


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
    otp = f"{secrets.randbelow(1_000_000):06d}"
    _driver_otp_store[payload.phone_number] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    # Send via WhatsApp
    from app.services.whatsapp_service import WhatsAppService
    message = f"🚚 *ZimAgriTrust Driver Verification*\n\nYour OTP code is: {otp}\n\nValid for 10 minutes. Do not share this code with anyone."
    try:
        await WhatsAppService.send_whatsapp_message(payload.phone_number, message)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to send WhatsApp OTP: {e}")

    # TODO: dispatch via Africa's Talking SMS in production
    # sms_service.send(payload.phone_number, f"Your ZimAgriTrust driver OTP: {otp}")
    import logging
    logging.getLogger(__name__).info("DRIVER OTP for %s: %s", payload.phone_number, otp)
    # Return OTP in response for development (remove in production)
    return {"status": "sent", "message": "OTP sent to your phone number", "otp": otp, "dev_note": "OTP returned for development only - remove in production"}


@driver_auth_router.post("/verify-otp", summary="Verify OTP and get temp registration token")
async def driver_verify_otp(
    payload: DriverOtpVerify,
    db: Session = Depends(get_db),
) -> dict:
    """Verify OTP; returns a short-lived temp_token for the registration form submission."""
    record = _driver_otp_store.get(payload.phone_number)
    if not record:
        raise HTTPException(status_code=400, detail="No OTP found for this number. Request a new one.")
    if datetime.now(timezone.utc) > record["expires_at"]:
        _driver_otp_store.pop(payload.phone_number, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if record["otp"] != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
    _driver_otp_store.pop(payload.phone_number, None)
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
