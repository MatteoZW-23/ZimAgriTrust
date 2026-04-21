from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token, TokenRefresh, UserLogin, UserRegister, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, Login2FA
)

from app.services.rate_limit_service import (
    clear_login_failures,
    enforce_rate_limit,
    ensure_login_not_locked,
    record_login_failure,
)
from app.services.notification_service import NotificationService
from app.services.auth_service import authenticate_user, register_user

router = APIRouter()

import random

# Simple in-memory OTP cache for demo (should be Redis in production)
OTP_CACHE = {}

@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset by sending a verification code via SMS and WhatsApp.
    """
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        return {"message": "Process initiated. If an account matches this number, a verification code will be sent."}
    
    otp = str(random.randint(100000, 999999))
    OTP_CACHE[payload.phone_number] = otp
    
    await NotificationService.send_verification_code(payload.phone_number, otp)
    
    return {
        "message": "Verification code sent to your registered phone number via SMS and WhatsApp.",
    }


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Confirms the OTP and updates the password.
    """
    cached_otp = OTP_CACHE.get(payload.phone_number)
    
    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User accounts not found.")
        
    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    OTP_CACHE.pop(payload.phone_number, None)
    
    return {"message": "Password updated successfully. You can now log in."}


@router.post("/register", response_model=UserResponse)
async def register(
    payload: UserRegister, request: Request, db: Session = Depends(get_db)
) -> User:
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:register:ip:{client_host}",
        limit=5,
        window_seconds=300,
        detail="Too many registration attempts from this origin",
    )
    await enforce_rate_limit(
        f"auth:register:phone:{payload.phone_number}",
        limit=3,
        window_seconds=600,
        detail="Too many registration attempts for this phone number",
    )
    existing = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    return register_user(db, payload)


@router.post("/login")
async def login(
    payload: UserLogin, request: Request, db: Session = Depends(get_db)
):
    """
    Step 1 of Login: Verify credentials and send 2FA code.
    """
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:login:ip:{client_host}",
        limit=20,
        window_seconds=300,
        detail="Too many login attempts from this origin",
    )
    
    await ensure_login_not_locked(payload.phone_number)
    user = authenticate_user(db, payload.phone_number, payload.password)
    
    if not user:
        failures = await record_login_failure(payload.phone_number)
        if failures >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone or password"
        )
        
    if not user.is_active:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
        
    # Credentials OK -> Send 2FA Code
    otp = str(random.randint(100000, 999999))
    OTP_CACHE[f"login_2fa:{payload.phone_number}"] = otp
    
    await NotificationService.send_verification_code(payload.phone_number, otp)
    
    return {
        "status": "2FA_REQUIRED",
        "message": "Verification code sent via SMS and WhatsApp.",
        "phone": payload.phone_number
    }


@router.post("/verify-login-2fa", response_model=Token)
async def verify_login_2fa(payload: "Login2FA", db: Session = Depends(get_db)):
    """
    Step 2 of Login: Verify 2FA code and return session tokens.
    """
    cached_otp = OTP_CACHE.get(f"login_2fa:{payload.phone_number}")
    
    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    await clear_login_failures(payload.phone_number)
    OTP_CACHE.pop(f"login_2fa:{payload.phone_number}", None)
    
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    return Token(
        access_token=access_token, 
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=Token)
async def refresh(payload: TokenRefresh, db: Session = Depends(get_db)) -> Token:
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = decoded.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.is_suspended:
            raise HTTPException(status_code=403, detail="Account suspended")

        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> dict:
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
