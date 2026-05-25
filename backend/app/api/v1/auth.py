"""
Comprehensive authentication API endpoints for ZimAgriTrust
Handles all authentication flows:
- PIN verification (USSD + App)
- Password authentication (Admins)
- MFA setup and verification
- Session management
- Token refresh
- Invitation acceptance
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.models.security_enhanced import (
    PINLockout, UserSession, TokenBlacklist, SecurityAuditLog, AuditLogAction,
    MFAConfiguration
)
from app.services.security_service import (
    PasswordHasher, PINHasher, PINValidator, SessionManager, TokenManager,
    PINManager, MFAManager, AuditLogger, DeviceFingerprint, RateLimiter,
    RateLimitKey
)
from app.services.notification_service import NotificationService
from app.services.invitation_service import InvitationService
from app.services.rbac_service import RBACService
from app.core.security_middleware import DeviceFingerprintMiddleware, ThreatDetector


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PINLoginRequest(BaseModel):
    """PIN login request (phone + PIN for USSD/App)"""
    phone_number: str
    pin: str
    channel: str = "app"  # 'ussd' or 'app'


class PINLoginResponse(BaseModel):
    """PIN login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordLoginRequest(BaseModel):
    """Password login request (admins)"""
    email: str
    password: str
    mfa_code: Optional[str] = None


class PasswordLoginResponse(BaseModel):
    """Password login response"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    mfa_required: bool = False
    mfa_session_token: Optional[str] = None
    expires_in: Optional[int] = None


class PINChangeRequest(BaseModel):
    """PIN change request"""
    current_pin: str
    new_pin: str
    new_pin_confirm: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: str


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation"""
    email: str
    reset_token: str
    new_password: str


class MFASetupRequest(BaseModel):
    """MFA setup request"""
    method: str = "totp"  # 'totp', 'hardware', 'sms'


class MFASetupResponse(BaseModel):
    """MFA setup response"""
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    backup_codes: Optional[list] = None
    setup_token: str


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    code: str
    setup_token: Optional[str] = None  # For MFA setup


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""
    all_sessions: bool = False  # Logout all sessions or just current


class InvitationAcceptRequest(BaseModel):
    """Accept invitation request"""
    email: str
    token: str
    password: str
    full_name: Optional[str] = None


class SelfRegistrationRequest(BaseModel):
    """Self-registration for farmers/buyers/drivers"""
    phone_number: str
    full_name: str
    pin: str
    role: str  # 'farmer', 'buyer', 'driver'
    agreement_accepted: bool


# ============================================================================
# AUTHENTICATION ROUTER
# ============================================================================

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


# ============================================================================
# PIN AUTHENTICATION (USSD + App)
# ============================================================================

@router.post("/login/pin", response_model=PINLoginResponse)
async def login_with_pin(
    request: PINLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate with PIN (works on USSD and Mobile App)
    
    Unified PIN system - same PIN works everywhere
    """
    
    # Extract IP and device info
    ip_address = DeviceFingerprintMiddleware.extract_ip(http_request)
    device_fingerprint = DeviceFingerprintMiddleware.generate_fingerprint(http_request)
    
    # Rate limiting check
    can_attempt, remaining = RateLimiter.check_limit(
        db, request.phone_number, RateLimitKey.PIN_ATTEMPTS
    )
    
    if not can_attempt:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many PIN attempts. Try again later.",
        )
    
    # Find user
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    
    if not user:
        # Record failed attempt
        RateLimiter.record_attempt(db, request.phone_number, RateLimitKey.PIN_ATTEMPTS)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or PIN",
        )
    
    # Verify PIN
    is_valid, error = PINManager.verify_pin(db, user, request.pin, request.channel, ip_address)
    
    if not is_valid:
        # Record failed attempt
        RateLimiter.record_attempt(db, request.phone_number, RateLimitKey.PIN_ATTEMPTS)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid PIN",
        )
    
    # Check if account is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )
    
    # Create tokens
    access_token, access_exp = TokenManager.create_access_token(user)
    refresh_token, refresh_exp = TokenManager.create_refresh_token(user)
    
    # Hash tokens for storage
    access_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Enforce concurrency limits
    SessionManager.enforce_concurrency_limit(db, user)
    
    # Create session
    session = SessionManager.create_session(
        db,
        user,
        access_token_hash,
        refresh_token_hash,
        ip_address,
        device_fingerprint,
        http_request.headers.get('user-agent'),
        http_request.headers.get('x-platform', 'app'),
    )
    
    # Log audit event
    AuditLogger.log(
        db,
        AuditLogAction.LOGIN,
        user_id=user.id,
        ip_address=ip_address,
        details={'channel': request.channel, 'method': 'pin'},
    )
    
    # Send notification
    await NotificationService.send_notification(
        db, user, 'new_login_detected',
        LOCATION='Your device',
        TIME=datetime.now(timezone.utc).isoformat(),
    )
    
    access_expiry = (access_exp - datetime.now(timezone.utc)).total_seconds() if isinstance(access_exp, datetime) else 3600
    
    return PINLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_expiry),
    )


# ============================================================================
# PASSWORD AUTHENTICATION (Admins)
# ============================================================================

@router.post("/login/password", response_model=PasswordLoginResponse)
async def login_with_password(
    request: PasswordLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email + password (for admins and staff)
    
    Supports MFA requirement
    """
    
    # Extract IP
    ip_address = DeviceFingerprintMiddleware.extract_ip(http_request)
    
    # Rate limiting
    can_attempt, _ = RateLimiter.check_limit(
        db, request.email, RateLimitKey.LOGIN_ATTEMPTS
    )
    
    if not can_attempt:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
        )
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        RateLimiter.record_attempt(db, request.email, RateLimitKey.LOGIN_ATTEMPTS)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Verify password
    pw_hasher = PasswordHasher()
    if not pw_hasher.verify_password(request.password, user.password_hash):
        RateLimiter.record_attempt(db, request.email, RateLimitKey.LOGIN_ATTEMPTS)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check if MFA required
    mfa_config = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == user.id).first()
    
    if mfa_config and mfa_config.status == 'active':
        # Generate MFA session token
        mfa_token, _ = TokenManager.create_token(
            TokenType.MFA,
            user.id,
            timedelta(minutes=5)
        )
        
        return PasswordLoginResponse(
            mfa_required=True,
            mfa_session_token=mfa_token,
        )
    
    # Create tokens
    access_token, access_exp = TokenManager.create_access_token(user)
    refresh_token, refresh_exp = TokenManager.create_refresh_token(user)
    
    # Create session
    device_fingerprint = DeviceFingerprintMiddleware.generate_fingerprint(http_request)
    access_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    SessionManager.create_session(
        db,
        user,
        access_token_hash,
        refresh_token_hash,
        ip_address,
        device_fingerprint,
        http_request.headers.get('user-agent'),
        'web',
    )
    
    # Log audit
    AuditLogger.log(
        db,
        AuditLogAction.LOGIN,
        user_id=user.id,
        ip_address=ip_address,
        details={'method': 'password'},
    )
    
    access_expiry = (access_exp - datetime.now(timezone.utc)).total_seconds()
    
    return PasswordLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_expiry),
    )


# ============================================================================
# PIN MANAGEMENT
# ============================================================================

@router.post("/pin/change")
async def change_pin(
    request: PINChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user PIN (unified across USSD and App)"""
    
    # Verify current PIN
    is_valid, error = PINManager.verify_pin(db, current_user, request.current_pin)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current PIN is incorrect",
        )
    
    # Validate new PIN
    is_valid, error = PINValidator.is_valid(request.new_pin, current_user.phone_number)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    # Verify confirmation
    if request.new_pin != request.new_pin_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN confirmation does not match",
        )
    
    # Create new PIN
    PINManager.create_pin(db, current_user, request.new_pin, "user_initiated")
    
    # Log audit
    AuditLogger.log(
        db,
        AuditLogAction.PIN_CHANGE,
        user_id=current_user.id,
        details={'reason': 'user_initiated'},
    )
    
    # Notify all channels
    await NotificationService.send_notification(
        db, current_user, 'pin_changed'
    )
    
    # Terminate all sessions (force re-login)
    SessionManager.terminate_all_sessions(db, current_user.id, 'pin_changed')
    
    return {"message": "PIN changed successfully"}


# ============================================================================
# MFA MANAGEMENT
# ============================================================================

@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: MFASetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Setup multi-factor authentication"""
    
    # Generate MFA session token for confirmation
    mfa_session_token, _ = TokenManager.create_token(
        TokenType.MFA,
        current_user.id,
        timedelta(minutes=10)
    )
    
    if request.method == "totp":
        result = MFAManager.enable_mfa(db, current_user)
        
        return MFASetupResponse(
            secret=result.get('secret'),
            qr_code=result.get('qr_code'),
            backup_codes=result.get('backup_codes'),
            setup_token=mfa_session_token,
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"MFA method not supported: {request.method}",
    )


@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify MFA code and complete setup"""
    
    # Verify code
    if MFAManager.verify_mfa(db, current_user, request.code):
        config = db.query(MFAConfiguration).filter(MFAConfiguration.user_id == current_user.id).first()
        config.status = 'active'
        config.enabled_at = datetime.now(timezone.utc)
        db.commit()
        
        # Send notification
        await NotificationService.send_notification(
            db, current_user, 'mfa_enabled'
        )
        
        return {"message": "MFA enabled successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid MFA code",
    )


# ============================================================================
# LOGOUT & SESSION MANAGEMENT
# ============================================================================

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """Logout user"""
    
    if request.all_sessions:
        # Logout all sessions
        SessionManager.terminate_all_sessions(db, current_user.id, 'logout')
    else:
        # Logout current session only
        auth_header = http_request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            TokenManager.blacklist_token(db, token, TokenType.ACCESS, current_user.id)
    
    # Log audit
    AuditLogger.log(
        db,
        AuditLogAction.LOGOUT,
        user_id=current_user.id,
    )
    
    return {"message": "Logged out successfully"}


# ============================================================================
# TOKEN REFRESH
# ============================================================================

@router.post("/token/refresh", response_model=PINLoginResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    payload = TokenManager.verify_token(request.refresh_token, TokenType.REFRESH)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get user
    user_id = uuid.UUID(payload['sub'])
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Create new access token
    access_token, access_exp = TokenManager.create_access_token(user)
    
    access_expiry = (access_exp - datetime.now(timezone.utc)).total_seconds()
    
    return PINLoginResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # Can reuse or generate new
        expires_in=int(access_expiry),
    )


# ============================================================================
# SELF-REGISTRATION
# ============================================================================

@router.post("/register/farmer")
async def register_farmer(
    request: SelfRegistrationRequest,
    db: Session = Depends(get_db),
):
    """Self-register as farmer"""
    
    if not request.agreement_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must accept terms and conditions",
        )
    
    from app.services.onboarding_service import SelfRegistrationService
    
    success, error, user = SelfRegistrationService.register_farmer(
        db,
        request.phone_number,
        request.full_name,
        request.pin,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    # Send welcome notification
    await NotificationService.send_notification(
        db, user, 'account_approved',
        ROLE='Farmer',
    )
    
    return {"message": "Registered successfully", "user_id": str(user.id)}


@router.post("/register/buyer")
async def register_buyer(
    request: SelfRegistrationRequest,
    db: Session = Depends(get_db),
):
    """Self-register as buyer"""
    
    if not request.agreement_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must accept terms and conditions",
        )
    
    from app.services.onboarding_service import SelfRegistrationService
    
    success, error, user = SelfRegistrationService.register_buyer(
        db,
        request.phone_number,
        request.full_name,
        request.pin,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    await NotificationService.send_notification(
        db, user, 'account_approved',
        ROLE='Buyer',
    )
    
    return {"message": "Registered successfully", "user_id": str(user.id)}


@router.post("/register/driver")
async def register_driver(
    request: SelfRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Self-register as driver
    Note: Driver cannot operate until documents are verified
    """
    
    if not request.agreement_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must accept terms and conditions",
        )
    
    from app.services.onboarding_service import SelfRegistrationService
    
    success, error, user = SelfRegistrationService.register_driver(
        db,
        request.phone_number,
        request.full_name,
        request.pin,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    # Driver must upload documents
    await NotificationService.send_notification(
        db, user, 'account_approved',
        ROLE='Driver',
    )
    
    return {
        "message": "Registered successfully. Please upload documents for verification.",
        "user_id": str(user.id),
        "status": "PENDING_VERIFICATION",
    }


# ============================================================================
# INVITATION ACCEPTANCE
# ============================================================================

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
        # Create user
        pw_hasher = PasswordHasher()
        user = User(
            email=request.email,
            full_name=request.full_name or '',
            password_hash=pw_hasher.hash_password(request.password),
            status=UserStatus.PENDING_VERIFICATION,
        )
        db.add(user)
        db.flush()
    else:
        # Update password
        pw_hasher = PasswordHasher()
        user.password_hash = pw_hasher.hash_password(request.password)
    
    # Accept invitation
    success, error = InvitationService.accept_invitation(db, invitation, user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    await NotificationService.send_notification(
        db, user, 'account_approved',
        ROLE=invitation.role.name,
    )
    
    return {"message": "Invitation accepted. You can now login."}


# ============================================================================
# DEPENDENCY INJECTION HELPERS
# ============================================================================

import hashlib
from app.models.security_enhanced import TokenType


async def get_current_user(
    http_request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token"""
    
    auth_header = http_request.headers.get('authorization', '')
    
    if not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    
    token = auth_header[7:]
    
    # Check if blacklisted
    if TokenManager.is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    
    # Verify token
    payload = TokenManager.verify_token(token, TokenType.ACCESS)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    user_id = uuid.UUID(payload['sub'])
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
