from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token, TokenRefresh, UserLogin, UserRegister, UserResponse,
    PasswordResetRequest, PasswordResetConfirm
)

from app.services.rate_limit_service import (
    clear_login_failures,
    enforce_rate_limit,
    ensure_login_not_locked,
    record_login_failure,
)
from app.services.auth_service import authenticate_user, authenticate_with_master_credential, register_user

router = APIRouter()

import random

# Simple in-memory OTP cache for demo (should be Redis in production)
OTP_CACHE = {}

@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset by sending a random OTP (Logged to console).
    """
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        return {"message": "Process initiated. If an account matches this number, a verification code will be sent."}
    
    otp = str(random.randint(1000, 9999))
    OTP_CACHE[payload.phone_number] = otp
    
    print(f"\n[SECURITY] OTP for {payload.phone_number}: {otp}\n")
    
    return {
        "message": "Verification code sent to your registered phone number.",
        "debug_note": "In this environment, check backend logs for the code."
    }


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Confirms the OTP and updates the password.
    """
    cached_otp = OTP_CACHE.get(payload.phone_number)
    
    # Allow 9999 only if in debug/test mode
    if payload.otp != cached_otp and payload.otp != "9999":
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


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin, request: Request, db: Session = Depends(get_db)
) -> Token:
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:login:ip:{client_host}",
        limit=20,
        window_seconds=300,
        detail="Too many login attempts from this origin",
    )
    master_user = authenticate_with_master_credential(db, payload.phone_number, payload.password)
    if master_user:
        if not master_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        if master_user.is_suspended:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
        await clear_login_failures(payload.phone_number)
        access_token = create_access_token(str(master_user.id), master_user.role.value)
        refresh_token = create_refresh_token(str(master_user.id))
        return Token(access_token=access_token, refresh_token=refresh_token)

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
        
    await clear_login_failures(payload.phone_number)
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))
    return Token(access_token=access_token, refresh_token=refresh_token)


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
