"""
Comprehensive Security & Authentication Endpoints for ZimAgriTrust

Covers:
- MFA setup (TOTP), verification, backup codes
- PIN change with validation
- Password change with history enforcement
- Supplier & Staff login flows
- Session management (logout, list sessions, revoke)
- Password/PIN reset
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.security_enhanced import (
    SecurityAuditLog,
    AuditLogAction,
    PasswordHistory,
)
from app.models.user import User, UserRole, UserStatus
from app.services.mfa_service import MFAService
from app.services.pin_validator import PINValidator
from app.services.portal_auth_service import (
    ADMIN_PORTAL_ROLES,
    SUPPLIER_ROLES,
    STAFF_ROLES,
    begin_mfa_login,
    complete_mfa_login,
    issue_session_token,
    login_with_pin,
    ensure_active_user,
    ensure_role,
)
from app.services.session_service import (
    revoke_session,
    revoke_all_user_sessions,
)
from app.services.rate_limit_service import enforce_rate_limit
from app.core.password_validator import PasswordValidator

# ── Routers ──────────────────────────────────────────────────────────────────
mfa_router = APIRouter()
security_router = APIRouter()
supplier_auth_router = APIRouter()
staff_auth_router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str
    issuer: str
    account: str


class MFAConfirmRequest(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)


class MFAConfirmResponse(BaseModel):
    success: bool
    backup_codes: list[str] = []
    message: str


class MFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8)
    is_backup_code: bool = False


class ChangePINRequest(BaseModel):
    current_pin: str = Field(..., min_length=4, max_length=6)
    new_pin: str = Field(..., min_length=4, max_length=6)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)


class SessionInfo(BaseModel):
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: str
    last_active_at: str
    is_current: bool = False


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]
    count: int


class RevokeSessionRequest(BaseModel):
    session_id: str


# ══════════════════════════════════════════════════════════════════════════════
# MFA ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@mfa_router.get("/status")
async def mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Check MFA status for current user"""
    config = MFAService.get_mfa_config(db, current_user.id)
    return {
        "mfa_enabled": MFAService.is_mfa_enabled(db, current_user.id),
        "mfa_required": MFAService.is_mfa_required(current_user),
        "mfa_allowed": MFAService.is_mfa_allowed(current_user),
        "needs_setup": MFAService.needs_mfa_setup(db, current_user),
        "backup_codes_remaining": MFAService.get_remaining_backup_codes_count(db, current_user.id),
        "status": config.status.value if config else "not_configured",
    }


@mfa_router.post("/setup", response_model=MFASetupResponse)
async def begin_mfa_setup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFASetupResponse:
    """Begin MFA setup — returns QR code and secret for authenticator app"""
    try:
        result = MFAService.begin_totp_setup(db, current_user)
        return MFASetupResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@mfa_router.post("/setup/confirm", response_model=MFAConfirmResponse)
async def confirm_mfa_setup(
    payload: MFAConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MFAConfirmResponse:
    """Confirm MFA setup by entering the first TOTP code from authenticator app"""
    success, backup_codes = MFAService.confirm_totp_setup(
        db, current_user, payload.totp_code
    )
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid TOTP code. Scan the QR code again and try with a fresh code.",
        )
    return MFAConfirmResponse(
        success=True,
        backup_codes=backup_codes or [],
        message="MFA enabled successfully. Save your backup codes securely.",
    )


@mfa_router.post("/verify")
async def verify_mfa_code(
    payload: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Verify a TOTP code or backup code"""
    ip = request.client.host if request.client else "unknown"

    await enforce_rate_limit(
        f"mfa:verify:{current_user.id}",
        limit=settings.RATE_LIMIT_MFA_ATTEMPTS,
        window_seconds=3600,
        detail="Too many MFA verification attempts",
    )

    if payload.is_backup_code:
        valid = MFAService.verify_backup_code(db, current_user, payload.code, ip)
    else:
        valid = MFAService.verify_totp(db, current_user, payload.code, ip)

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    return {"verified": True}


@mfa_router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Regenerate backup codes (invalidates old ones)"""
    codes = MFAService.regenerate_backup_codes(db, current_user)
    if codes is None:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    return {
        "backup_codes": codes,
        "message": "New backup codes generated. Old codes are now invalid.",
    }


@mfa_router.post("/disable")
async def disable_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Disable MFA (only if optional for this role)"""
    try:
        MFAService.disable_mfa(db, current_user, actor=current_user)
        return {"disabled": True, "message": "MFA has been disabled"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# PIN CHANGE ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@security_router.post("/change-pin")
async def change_pin(
    payload: ChangePINRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change PIN for farmers, buyers, drivers, and agents"""
    # Only PIN-based roles
    pin_roles = {
        UserRole.FARMER, UserRole.BUYER, UserRole.DRIVER,
        UserRole.AGENT,
    }
    if current_user.role not in pin_roles:
        raise HTTPException(status_code=403, detail="PIN change not applicable for your role")

    # Verify current PIN
    if not current_user.ussd_pin_hash or not verify_password(
        payload.current_pin, current_user.ussd_pin_hash
    ):
        raise HTTPException(status_code=401, detail="Current PIN is incorrect")

    # Validate new PIN
    is_valid, error = PINValidator.validate_and_check_history(
        db,
        current_user.id,
        payload.new_pin,
        phone_number=current_user.phone_number,
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Hash and save
    new_hash = get_password_hash(payload.new_pin)
    PINValidator.record_pin_change(db, current_user.id, new_hash, reason="user_initiated")

    current_user.ussd_pin_hash = new_hash
    current_user.password_hash = new_hash  # Unified PIN
    current_user.must_change_password = False
    current_user.password_changed_at = datetime.now(timezone.utc)

    # Audit log
    audit = SecurityAuditLog(
        action=AuditLogAction.PIN_CHANGE,
        user_id=current_user.id,
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        details={"channel": "api"},
        status="success",
    )
    db.add(audit)
    db.commit()

    # Revoke other sessions
    await revoke_all_user_sessions(
        db, current_user.id, reason="pin_change"
    )

    return {"message": "PIN changed successfully. All other sessions have been terminated."}


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD CHANGE ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@security_router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change password for admins, suppliers, and staff"""
    password_roles = {
        UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN,
        UserRole.FINANCE_ADMIN, UserRole.REGIONAL_ADMIN, UserRole.REGIONAL_MANAGER,
        UserRole.SUPPORT_ADMIN, UserRole.BRANCH_ADMIN, UserRole.SUPPLIER,
        UserRole.STAFF,
    }
    if current_user.role not in password_roles:
        raise HTTPException(status_code=403, detail="Password change not applicable for your role")

    # Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Validate new password strength
    is_valid, error = PasswordValidator.validate(payload.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Check password history (last 5)
    recent_passwords = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == current_user.id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(settings.PASSWORD_HISTORY_COUNT)
        .all()
    )
    for ph in recent_passwords:
        if verify_password(payload.new_password, ph.password_hash):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reuse your last {settings.PASSWORD_HISTORY_COUNT} passwords",
            )

    # Hash and save
    new_hash = get_password_hash(payload.new_password)

    # Record old password in history
    history = PasswordHistory(
        user_id=current_user.id,
        password_hash=current_user.password_hash,
    )
    db.add(history)

    current_user.password_hash = new_hash
    current_user.must_change_password = False
    current_user.must_change_password_reason = None
    current_user.password_changed_at = datetime.now(timezone.utc)

    # Audit log
    audit = SecurityAuditLog(
        action=AuditLogAction.PASSWORD_CHANGE,
        user_id=current_user.id,
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        details={"channel": "api"},
        status="success",
    )
    db.add(audit)
    db.commit()

    # Revoke other sessions
    await revoke_all_user_sessions(
        db, current_user.id, reason="password_change"
    )

    return {"message": "Password changed successfully. All other sessions have been terminated."}


# ══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@security_router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """List all active sessions for current user"""
    from app.models.session import UserSession

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .order_by(UserSession.created_at.desc())
        .all()
    )

    return SessionListResponse(
        sessions=[
            SessionInfo(
                id=str(s.id),
                ip_address=s.ip_address,
                user_agent=s.user_agent[:200] if s.user_agent else None,
                created_at=s.created_at.isoformat() if s.created_at else "",
                last_active_at=s.last_active_at.isoformat() if s.last_active_at else "",
            )
            for s in sessions
        ],
        count=len(sessions),
    )


@security_router.post("/sessions/revoke")
async def revoke_specific_session(
    payload: RevokeSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke a specific session"""
    from app.models.session import UserSession

    session = db.query(UserSession).filter(
        UserSession.id == uuid.UUID(payload.session_id),
        UserSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await revoke_session(db, session.id, reason="user_revoked")
    return {"revoked": True, "session_id": payload.session_id}


@security_router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke all sessions except current"""
    count = await revoke_all_user_sessions(
        db, current_user.id, reason="user_revoke_all"
    )
    return {"revoked_count": count, "message": "All other sessions terminated"}


@security_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Logout — revoke current session and clear cookies"""
    from app.models.session import UserSession

    # Find session by current access token JTI
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        from app.core.security import decode_token
        try:
            payload = decode_token(auth_header[7:])
            jti = payload.get("jti")
            if jti:
                session = db.query(UserSession).filter(
                    UserSession.access_token_jti == jti,
                    UserSession.user_id == current_user.id,
                ).first()
                if session:
                    await revoke_session(db, session.id, reason="logout")
        except Exception:
            pass

    # Audit
    audit = SecurityAuditLog(
        action=AuditLogAction.LOGOUT,
        user_id=current_user.id,
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        status="success",
    )
    db.add(audit)
    db.commit()

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")

    return {"message": "Logged out successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIER AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@supplier_auth_router.post("/login")
async def supplier_login(
    payload: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """Email + Password login for suppliers"""
    from app.schemas.auth import Token, UserLogin

    email = payload.get("email", "")
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:supplier:ip:{client_host}",
        limit=10,
        window_seconds=300,
        detail="Too many login attempts",
    )

    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    ensure_role(user, SUPPLIER_ROLES, "supplier")
    ensure_active_user(user)

    return await issue_session_token(
        db=db, user=user, request=request, response=response
    )


# ══════════════════════════════════════════════════════════════════════════════
# STAFF AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@staff_auth_router.post("/login")
async def staff_login(
    payload: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """Email + Password login for staff members"""
    email = payload.get("email", "")
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    client_host = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"auth:staff:ip:{client_host}",
        limit=10,
        window_seconds=300,
        detail="Too many login attempts",
    )

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    ensure_role(user, STAFF_ROLES | ADMIN_PORTAL_ROLES, "staff")
    ensure_active_user(user)

    # Check if MFA is required
    from app.services.mfa_service import MFAService
    if MFAService.needs_mfa_setup(db, user):
        return {
            "status": "MFA_SETUP_REQUIRED",
            "message": "You must set up MFA before accessing the system.",
            "temp_token": None,  # Frontend should redirect to MFA setup
        }

    if MFAService.is_mfa_enabled(db, user.id):
        # Send SMS OTP as secondary verification
        from app.services.portal_auth_service import set_otp
        from app.services.notification_service import NotificationService
        import random

        otp = str(random.randint(100000, 999999))
        await set_otp(f"staff:mfa:{user.phone_number}", otp)
        await NotificationService.send_verification_code(user.phone_number, otp)

        return {
            "status": "MFA_REQUIRED",
            "message": "Verification code sent.",
            "phone": user.phone_number,
        }

    return await issue_session_token(
        db=db, user=user, request=request, response=response
    )
