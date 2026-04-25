from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token, TokenRefresh, UserLogin, UserRegister, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, Login2FA,
    ProfileUpdate, NotificationPrefsUpdate, ChangePinRequest
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

# OTP helpers — backed by Redis so they survive restarts and scale horizontally
from app.services.cache_service import cache_service

OTP_TTL = 300  # 5 minutes

async def _set_otp(key: str, otp: str):
    await cache_service.set(f"otp:{key}", otp, expire=OTP_TTL)

async def _get_otp(key: str) -> str | None:
    return await cache_service.get(f"otp:{key}")

async def _clear_otp(key: str):
    await cache_service.delete(f"otp:{key}")

@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset by sending a verification code via SMS and WhatsApp.
    """
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        return {"message": "Process initiated. If an account matches this number, a verification code will be sent."}
    
    otp = str(random.randint(100000, 999999))
    await _set_otp(payload.phone_number, otp)
    
    await NotificationService.send_verification_code(payload.phone_number, otp)
    
    return {
        "message": "Verification code sent to your registered phone number via SMS and WhatsApp.",
    }


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Confirms the OTP and updates the password.
    """
    cached_otp = await _get_otp(payload.phone_number)
    
    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User accounts not found.")
    
    hashed_pin = get_password_hash(payload.new_password)
    user.password_hash = hashed_pin
    user.ussd_pin_hash = hashed_pin  # Update USSD PIN to match
    user.must_change_password = False  # Clear forced change flag if set
    db.commit()
    await _clear_otp(payload.phone_number)
    
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
    await _set_otp(f"login_2fa:{payload.phone_number}", otp)
    
    await NotificationService.send_verification_code(payload.phone_number, otp)
    
    return {
        "status": "2FA_REQUIRED",
        "message": "Verification code sent via SMS and WhatsApp.",
        "phone": payload.phone_number
    }


@router.post("/verify-login-2fa", response_model=Token)
async def verify_login_2fa(payload: "Login2FA", response: Response, db: Session = Depends(get_db)):
    """
    Step 2 of Login: Verify 2FA code and return session tokens.
    """
    cached_otp = await _get_otp(f"login_2fa:{payload.phone_number}")
    
    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    await clear_login_failures(payload.phone_number)
    await _clear_otp(f"login_2fa:{payload.phone_number}")
    
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        secure=True, 
        samesite="lax",
        max_age=15 * 60
    )
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        secure=True, 
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return Token(
        access_token=access_token, 
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=Token)
async def refresh(request: Request, response: Response, payload: TokenRefresh = None, db: Session = Depends(get_db)) -> Token:
    token = request.cookies.get("refresh_token")
    if not token and payload:
        token = payload.refresh_token
        
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    try:
        decoded = decode_token(token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        jti = decoded.get("jti")
        from app.services.cache_service import cache_service
        if await cache_service.get(f"blacklist_{jti}"):
            raise HTTPException(status_code=401, detail="Refresh token revoked")
            
        # Blacklist old refresh token
        exp = decoded.get("exp")
        import time
        now = int(time.time())
        ttl = exp - now
        if ttl > 0:
            await cache_service.set(f"blacklist_{jti}", "true", expire=ttl)

        user_id = decoded.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.is_suspended:
            raise HTTPException(status_code=403, detail="Account suspended")

        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id))
        
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="lax", max_age=15 * 60)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=7 * 24 * 60 * 60)
        
        return Token(access_token=access_token, refresh_token=refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            import time
            now = int(time.time())
            ttl = exp - now
            if ttl > 0:
                from app.services.cache_service import cache_service
                await cache_service.set(f"blacklist_{jti}", "true", expire=ttl)
        except Exception:
            pass
            
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/change-pin", response_model=UserResponse)
def change_pin(
    payload: ChangePinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Change PIN — required on first login when must_change_password=True.
    Also available any time a user wants to update their PIN.
    """
    if not verify_password(payload.current_pin, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current PIN is incorrect.")

    if payload.current_pin == payload.new_pin:
        raise HTTPException(status_code=400, detail="New PIN must be different from the current PIN.")

    hashed = get_password_hash(payload.new_pin)
    current_user.password_hash = hashed
    current_user.ussd_pin_hash = hashed
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update the current user's profile fields."""
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/notifications", response_model=UserResponse)
def update_notification_prefs(
    payload: NotificationPrefsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update the current user's notification preferences."""
    existing = current_user.notification_prefs or {}
    updates = payload.model_dump(exclude_none=True)
    merged = {**existing, **updates}
    current_user.notification_prefs = merged
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/deactivate", response_model=UserResponse)
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Deactivate the current user's account (soft disable)."""
    current_user.is_active = False
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/account", response_model=UserResponse)
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """GDPR-compliant account deletion: anonymize PII and close account."""
    import uuid as _uuid
    from app.models.user import UserStatus

    current_user.full_name = "DELETED_USER"
    current_user.phone_number = f"DELETED_{str(_uuid.uuid4())[:8]}"
    current_user.email = None
    current_user.national_id = None
    current_user.status = UserStatus.CLOSED
    current_user.is_active = False
    db.commit()
    db.refresh(current_user)
    return current_user
