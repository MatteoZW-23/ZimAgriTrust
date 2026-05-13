from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, get_password_hash,
    verify_password, check_password_strength, is_common_password, check_password_history,
    generate_email_verification_token,
)
from app.services.session_service import create_session, revoke_all_user_sessions
from app.models.user import User, UserRole, UserStatus
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
from app.services.auth_service import authenticate_user, register_user, build_phone_lookup_candidates
from app.services.portal_auth_service import PUBLIC_MOBILE_ROLES
from app.services.invitation_service import InvitationService
from app.services.security_service import PasswordHasher

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
    Confirms the OTP and updates the password/PIN.
    Staff (Admin/Agent): Updates password_hash (for password + MFA login)
    Farmers/Buyers: Updates ussd_pin_hash (for PIN-only login)
    """
    cached_otp = await _get_otp(payload.phone_number)
    
    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User accounts not found.")
    
    public_pin_roles = {UserRole.FARMER, UserRole.BUYER, UserRole.TRANSPORTER}
    if user.role in public_pin_roles:
        if not payload.new_password.isdigit() or not 4 <= len(payload.new_password) <= 6:
            raise HTTPException(status_code=400, detail="PIN must be 4-6 numeric digits.")
    else:
        password_check = check_password_strength(payload.new_password)
        if not password_check["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Password does not meet requirements: {', '.join(password_check['issues'])}"
            )

        if is_common_password(payload.new_password):
            raise HTTPException(
                status_code=400,
                detail="Password is too common. Please choose a stronger password."
            )

    # Enforce password history (for staff only)
    if user.role in {UserRole.ADMIN, UserRole.AGENT}:
        history = user.password_history or []
        if not check_password_history(payload.new_password, history, settings.PASSWORD_HISTORY_COUNT):
            raise HTTPException(
                status_code=400,
                detail="You cannot reuse a recent password. Please choose a new one."
            )
        # Store previous hash in history
        history.append(user.password_hash)
        user.password_history = history[-settings.PASSWORD_HISTORY_COUNT:]

    hashed_pin = get_password_hash(payload.new_password)

    # Update appropriate credential field based on role
    if user.role in {UserRole.ADMIN, UserRole.AGENT}:
        user.password_hash = hashed_pin
    else:
        user.ussd_pin_hash = hashed_pin

    user.must_change_password = False
    user.must_change_password_reason = None
    from datetime import datetime, timezone
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()
    await _clear_otp(payload.phone_number)

    # Revoke all sessions for security after password reset
    await revoke_all_user_sessions(db, user.id, reason="password_reset")

    # F#287 — security alert email after password reset (best-effort).
    if user.email:
        try:
            from app.services.email_service import email_service
            email_service.send_template(
                "email.security_alert",
                to=user.email,
                context={
                    "name": user.full_name,
                    "event": "Password reset completed",
                    "ip": "unknown",
                    "reset_link": "https://zimagritrust.co.zw/login",
                },
            )
        except Exception:  # noqa: BLE001
            pass

    return {"message": "Password updated successfully. All other sessions have been logged out for security."}


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
    if payload.role not in PUBLIC_MOBILE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privileged accounts must be created from the isolated admin portal.",
        )
    return register_user(db, payload)


@router.post("/login")
async def login(
    payload: UserLogin, request: Request, db: Session = Depends(get_db)
):
    """
    Deprecated shared staff login.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Shared staff login is disabled. Use /admin/login or /agent/login.",
    )
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
        
    # Ensure only staff use this endpoint
    if user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers and buyers should use PIN login. Please use the mobile app or USSD."
        )
        
    from app.models.user import UserStatus
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"ACCOUNT_PENDING: Your profile status is '{user.status}'. Access restricted until Super Admin verification."
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


@router.post("/login-pin")
async def login_pin(
    payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)
):
    """
    PIN Login for Farmers and Buyers: PIN-only authentication (no MFA).
    Admins and Agents should use /login endpoint instead.
    """
    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:login-pin:ip:{client_host}",
        limit=20,
        window_seconds=300,
        detail="Too many login attempts from this origin",
    )
    
    await ensure_login_not_locked(payload.phone_number)
    
    # Find user
    candidates = build_phone_lookup_candidates(payload.phone_number)
    user = db.query(User).filter(User.phone_number.in_(candidates)).first()
    
    if not user:
        failures = await record_login_failure(payload.phone_number)
        if failures >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone or PIN"
        )
    
    # Ensure only farmers/buyers use this endpoint
    if user.role in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff should use password login with MFA. Please use the admin dashboard."
        )
    
    # Verify PIN
    if not user.ussd_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No PIN set. Please register via mobile app."
        )
    
    if not verify_password(payload.password, user.ussd_pin_hash):
        failures = await record_login_failure(payload.phone_number)
        if failures >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect PIN"
        )
        
    from app.models.user import UserStatus
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"ACCOUNT_PENDING: Your profile status is '{user.status}'. Access restricted until Super Admin verification."
        )
        
    if not user.is_active:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    await clear_login_failures(payload.phone_number)

    # Create tokens directly (no MFA for PIN login)
    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    # Decode to get JTI for session tracking
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    # Create tracked session
    client_ip = request.client.host if request.client else "unknown"
    headers = dict(request.headers)
    await create_session(
        db=db,
        user_id=user.id,
        access_token_jti=access_payload.get("jti"),
        refresh_token_jti=refresh_payload.get("jti"),
        request_headers=headers,
        ip_address=client_ip,
    )

    # Set cookies
    cookie_secure = bool(settings.FORCE_HTTPS)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)

    # Set CSRF token
    import secrets as _secrets
    csrf_token = _secrets.token_urlsafe(32)
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=cookie_secure, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    response.headers["X-CSRF-Token"] = csrf_token

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        must_change_password=False,
    )


@router.post("/verify-login-2fa", response_model=Token)
async def verify_login_2fa(payload: "Login2FA", request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Deprecated shared MFA verification.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Shared MFA verification is disabled. Use /admin/verify-mfa or /agent/verify-mfa.",
    )
    cached_otp = await _get_otp(f"login_2fa:{payload.phone_number}")

    if not cached_otp or payload.otp != cached_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Mark phone as verified upon successful OTP validation for Admins/Staff
    if user.role in {UserRole.ADMIN, UserRole.AGENT} and not user.is_phone_verified:
        from datetime import datetime, timezone
        user.is_phone_verified = True
        user.phone_verified_at = datetime.now(timezone.utc)
        db.commit()

    await clear_login_failures(payload.phone_number)
    await _clear_otp(f"login_2fa:{payload.phone_number}")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    # Decode to get JTI for session tracking
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)

    # Create tracked session with device fingerprinting
    client_ip = request.client.host if request.client else "unknown"
    headers = dict(request.headers)
    await create_session(
        db=db,
        user_id=user.id,
        access_token_jti=access_payload.get("jti"),
        refresh_token_jti=refresh_payload.get("jti"),
        request_headers=headers,
        ip_address=client_ip,
    )

    # Set cookies
    cookie_secure = bool(settings.FORCE_HTTPS)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)

    # Set CSRF token cookie for subsequent state-changing requests
    import secrets as _secrets
    csrf_token = _secrets.token_urlsafe(32)
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=cookie_secure, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    response.headers["X-CSRF-Token"] = csrf_token

    # Check password expiry
    from datetime import datetime, timedelta, timezone
    must_change = False
    if user.password_changed_at:
        age_days = (datetime.now(timezone.utc) - user.password_changed_at).days
        if age_days >= settings.PASSWORD_EXPIRY_DAYS:
            must_change = True
            user.must_change_password = True
            user.must_change_password_reason = "expired"
            db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        must_change_password=must_change,
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
        
        cookie_secure = bool(settings.FORCE_HTTPS)
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=cookie_secure, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)
        
        return Token(access_token=access_token, refresh_token=refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
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
                # Also revoke in session table
                from app.services.session_service import revoke_session
                from app.models.session import UserSession
                session = db.query(UserSession).filter(UserSession.access_token_jti == jti).first()
                if session:
                    await revoke_session(db, session.id, reason="logout")
        except Exception:
            pass

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_devices(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Revoke all active sessions across all devices."""
    token = request.cookies.get("access_token")
    current_jti = None
    if token:
        try:
            payload = decode_token(token)
            current_jti = payload.get("jti")
        except Exception:
            pass

    from app.services.session_service import revoke_all_user_sessions
    revoked = await revoke_all_user_sessions(db, current_user.id, reason="user_logout_all")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")
    return {"message": f"Logged out from all {revoked} devices."}


@router.post("/verify-email-request")
async def request_email_verification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Request an email verification token to be sent (placeholder for email provider)."""
    if current_user.email_verified:
        return {"message": "Email already verified."}
    if not current_user.email:
        raise HTTPException(status_code=400, detail="No email on file. Update profile first.")

    token = generate_email_verification_token()
    current_user.email_verification_token = token
    db.commit()

    # In production: send email via SMTP/SES
    # For now: return token in dev mode or log it
    return {
        "message": "Verification email sent. Check your inbox.",
        "dev_token": token,  # REMOVE in production — for testing only
    }


@router.post("/verify-email/{token}")
async def confirm_email_verification(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Confirm email verification with the token from the email link."""
    if current_user.email_verified:
        return {"message": "Email already verified."}
    if current_user.email_verification_token != token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")

    from datetime import datetime, timezone
    current_user.email_verified = True
    current_user.email_verified_at = datetime.now(timezone.utc)
    current_user.email_verification_token = None
    db.commit()
    return {"message": "Email verified successfully."}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/change-pin", response_model=UserResponse)
async def change_pin(
    payload: ChangePinRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Change PIN/PASSWORD — role-based credential update.
    Staff (Admin/Agent): Updates password_hash (for password + MFA login)
    Farmers/Buyers: Updates ussd_pin_hash (for PIN-only login)
    """
    # Verify current credential based on role
    if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
        # Staff: Verify against password_hash
        if not verify_password(payload.current_pin, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        credential_field = "password_hash"
    else:
        # Farmers/Buyers: Verify against ussd_pin_hash
        if not current_user.ussd_pin_hash or not verify_password(payload.current_pin, current_user.ussd_pin_hash):
            raise HTTPException(status_code=400, detail="Current PIN is incorrect.")
        credential_field = "ussd_pin_hash"

    if payload.current_pin == payload.new_pin:
        raise HTTPException(status_code=400, detail="New PIN must be different from the current PIN.")

    public_pin_roles = {UserRole.FARMER, UserRole.BUYER, UserRole.TRANSPORTER}
    if current_user.role in public_pin_roles:
        if not payload.new_pin.isdigit() or not 4 <= len(payload.new_pin) <= 6:
            raise HTTPException(status_code=400, detail="PIN must be 4-6 numeric digits.")
    else:
        pw_check = check_password_strength(payload.new_pin)
        if not pw_check["valid"]:
            raise HTTPException(status_code=400, detail=f"Password too weak: {', '.join(pw_check['issues'])}")

        if is_common_password(payload.new_pin):
            raise HTTPException(status_code=400, detail="Password is too common. Choose a stronger one.")

    # Enforce password history (for staff only)
    if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
        history = current_user.password_history or []
        if not check_password_history(payload.new_pin, history, settings.PASSWORD_HISTORY_COUNT):
            raise HTTPException(status_code=400, detail="You cannot reuse a recent password. Please choose a new one.")
        # Store previous hash in history
        history.append(current_user.password_hash)
        current_user.password_history = history[-settings.PASSWORD_HISTORY_COUNT:]

    hashed = get_password_hash(payload.new_pin)

    # Update appropriate credential field based on role
    if current_user.role in {UserRole.ADMIN, UserRole.AGENT}:
        current_user.password_hash = hashed
    else:
        current_user.ussd_pin_hash = hashed

    current_user.must_change_password = False
    current_user.must_change_password_reason = None
    from datetime import datetime, timezone
    current_user.password_changed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    # Revoke all other active sessions for security
    from app.services.session_service import revoke_all_user_sessions
    await revoke_all_user_sessions(db, current_user.id, reason="password_change")

    return current_user


@router.post("/pin/change", response_model=UserResponse)
async def change_pin_mobile_alias(
    payload: ChangePinRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    return await change_pin(payload=payload, request=request, db=db, current_user=current_user)


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update the current user's profile fields."""
    update_data = payload.model_dump(exclude_none=True)
    new_email = update_data.get("email")
    if new_email and new_email != current_user.email:
        existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email address is already in use")
        current_user.email_verified = False
        current_user.email_verified_at = None
        current_user.email_verification_token = None
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


@router.get("/data-export")
def export_personal_data(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Export the current user's personal account data in portable JSON format."""
    return {
        "account": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "email": current_user.email,
            "role": current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
            "status": current_user.status.value if hasattr(current_user.status, "value") else current_user.status,
            "is_active": current_user.is_active,
            "is_phone_verified": current_user.is_phone_verified,
            "trust_score": current_user.trust_score,
            "preferred_language": current_user.preferred_language,
            "province": current_user.province,
            "district": current_user.district,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if getattr(current_user, "updated_at", None) else None,
        },
        "privacy": {
            "notification_prefs": current_user.notification_prefs or {},
            "email_verified": current_user.email_verified,
            "phone_verified_at": current_user.phone_verified_at.isoformat() if current_user.phone_verified_at else None,
        },
        "security": {
            "mfa_enabled": current_user.mfa_enabled,
            "password_changed_at": current_user.password_changed_at.isoformat() if current_user.password_changed_at else None,
            "must_change_password": current_user.must_change_password,
        },
    }


@router.post("/deactivate", response_model=UserResponse)
async def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Deactivate the current user's account (soft disable)."""
    current_user.is_active = False
    db.commit()
    db.refresh(current_user)
    await revoke_all_user_sessions(db, current_user.id, reason="account_deactivated")
    return current_user


@router.delete("/account", response_model=UserResponse)
async def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """GDPR-compliant account deletion: anonymize PII and close account."""
    import uuid as _uuid
    from app.models.user import UserStatus

    current_user.full_name = "DELETED_USER"
    current_user.phone_number = f"DEL{_uuid.uuid4().hex[:12]}"
    current_user.email = None
    current_user.national_id = None
    current_user.id_document_url = None
    current_user.email_verified = False
    current_user.email_verified_at = None
    current_user.email_verification_token = None
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.notification_prefs = {}
    current_user.province = None
    current_user.district = None
    current_user.ward = None
    current_user.latitude = None
    current_user.longitude = None
    current_user.status = UserStatus.CLOSED
    current_user.is_active = False
    db.commit()
    db.refresh(current_user)
    await revoke_all_user_sessions(db, current_user.id, reason="account_deleted")
    return current_user


# ============================================================================
# INVITATION ACCEPTANCE
# ============================================================================

from pydantic import BaseModel as _BaseModel

class InvitationAcceptRequest(_BaseModel):
    """Accept invitation request"""
    email: str
    token: str
    password: str
    full_name: str = ""
    phone_number: str = ""


@router.post("/invitation/accept")
async def accept_invitation(
    request: InvitationAcceptRequest,
    db: Session = Depends(get_db),
):
    """Accept invitation to join as admin/staff"""

    # Verify invitation
    is_valid, error, invitation = InvitationService.verify_invitation(
        db,
        request.email,
        request.token,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Check if user already exists
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        pw_hasher = PasswordHasher()
        # Map invitation RBAC role name to UserRole enum
        role_name = invitation.role.name.upper() if invitation.role else "ADMIN"
        role_map = {v.name: v for v in UserRole}
        user_role = role_map.get(role_name, UserRole.ADMIN)

        user = User(
            email=request.email,
            full_name=request.full_name or '',
            phone_number=request.phone_number or '',
            password_hash=pw_hasher.hash_password(request.password),
            status=UserStatus.PENDING_VERIFICATION,
            role=user_role,
            role_id=invitation.role_id,
        )
        db.add(user)
        db.flush()
    else:
        pw_hasher = PasswordHasher()
        user.password_hash = pw_hasher.hash_password(request.password)

    # Accept invitation
    success, error = InvitationService.accept_invitation(db, invitation, user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return {
        "message": "Invitation accepted. You can now login.",
        "role": invitation.role.name if invitation.role else "",
    }
