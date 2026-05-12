import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import UserResponse, UserRegister
from app.models.system_audit import SystemAudit
from app.services.notification_service import NotificationService

router = APIRouter()


def _audit_admin_id(admin: User):
    return admin.id if isinstance(admin.id, uuid.UUID) else None


def _audit_actor_details(admin: User) -> dict:
    return {
        "actor_id": str(admin.id),
        "actor_role": getattr(admin.role, "value", str(admin.role)),
    }


async def _notify_user(phone: str, name: str, action: str, reason: str):
    """Fire-and-forget notification to user via WhatsApp + SMS."""
    name = name or "User"

    messages = {
        "SUSPENDED": (
            f" *Account Suspended*\n\n"
            f"Hello {name}, your ZimAgritrust account has been suspended.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Contact support to appeal this decision."
        ),
        "ACTIVE": (
            f" *Account Reinstated*\n\n"
            f"Hello {name}, your ZimAgritrust account has been reactivated.\n\n"
            f"*Reason:* {reason}\n\n"
            f"You can now log in and resume trading."
        ),
        "FLAGGED": (
            f" *Account Flagged*\n\n"
            f"Hello {name}, your account has been flagged for review.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Some features may be restricted until review is complete."
        ),
        "CLOSED": (
            f" *Account Closed*\n\n"
            f"Hello {name}, your ZimAgritrust account has been permanently closed.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Contact support if you believe this is an error."
        ),
        "VERIFIED": (
            f" *Identity Verified*\n\n"
            f"Hello {name}, your identity has been verified by ZimAgritrust.\n\n"
            f"Your trust score has been updated. You now have full platform access."
        ),
        "VERIFY_REJECTED": (
            f" *Verification Rejected*\n\n"
            f"Hello {name}, your identity verification was rejected.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Please resubmit with a clearer ID document."
        ),
        "TRUST_UP": (
            f" *Trust Score Updated*\n\n"
            f"Hello {name}, your trust score has been adjusted by an administrator.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Check your dashboard for your new score."
        ),
        "TRUST_DOWN": (
            f" *Trust Score Reduced*\n\n"
            f"Hello {name}, your trust score has been reduced by an administrator.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Complete successful transactions to recover your score."
        ),
        "ROLE_CHANGED": (
            f" *Account Role Updated*\n\n"
            f"Hello {name}, your account role has been changed by an administrator.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Log out and back in to see your updated access."
        ),
        "DELETED": (
            f" *Account Removed*\n\n"
            f"Hello {name}, your ZimAgritrust account has been permanently removed.\n\n"
            f"*Reason:* {reason}\n\n"
            f"Contact support if you believe this is an error."
        ),
    }

    msg = messages.get(action, f"ZimAgritrust: Your account has been updated. Reason: {reason}")
    await NotificationService._notify_both_channels(phone, msg)

@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    role: Optional[UserRole] = None,
    verify_status: Optional[bool] = None,
    min_trust: Optional[float] = None,
    search: Optional[str] = None, # Handles Name, Phone, ID
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """
    Functions 1-8: View all users with advanced filtering and search.
    """
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if verify_status is not None:
        query = query.filter(User.id_verified == verify_status)
    if min_trust is not None:
        query = query.filter(User.trust_score >= min_trust)
    if search:
        # Search by Name, Phone, or ID
        search_filter = (
            (User.full_name.ilike(f"%{search}%")) | 
            (User.phone_number.ilike(f"%{search}%"))
        )
        try:
            uid = uuid.UUID(search)
            search_filter |= (User.id == uid)
        except ValueError:
            pass
        query = query.filter(search_filter)
        
    return query.all()

@router.post("/bulk-verify")
def bulk_verify_users(
    user_ids: list[uuid.UUID],
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 16: Bulk verification of identities (previously implemented).
    """
    updated = db.query(User).filter(User.id.in_(user_ids)).update({"id_verified": True}, synchronize_session=False)
    
    audit = SystemAudit(
        admin_id=_audit_admin_id(admin),
        action="USER_BULK_VERIFY",
        target_type="BATCH",
        target_id=None,
        note=f"Bulk verified {updated} users",
        details=_audit_actor_details(admin)
    )
    db.add(audit)
    db.commit()
    return {"verified_count": updated}

@router.post("/{user_id}/verify-reject")
def reject_verification(
    user_id: uuid.UUID,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.id_verified = False
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="VERIFICATION_REJECT", target_type="USER", target_id=user.id, note=reason, details=_audit_actor_details(admin))
    db.add(audit)
    db.commit()
    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, "VERIFY_REJECTED", reason)
    return {"status": "Verification rejected"}

@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: uuid.UUID,
    new_password: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 25: Reset user password manually.
    """
    from app.core.security import get_password_hash
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(new_password)
    
    audit = SystemAudit(
        admin_id=_audit_admin_id(admin),
        action="USER_PASSWORD_RESET",
        target_type="USER",
        target_id=user.id,
        note="Manual admin override of password",
        details=_audit_actor_details(admin)
    )
    db.add(audit)
    db.commit()
    return {"status": "Password changed successfully"}

@router.patch("/{user_id}/role")
def change_user_role(
    user_id: uuid.UUID,
    new_role: UserRole,
    reason: str = "Administrative role update",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_role = user.role
    user.role = new_role
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="USER_ROLE_CHANGE", target_type="USER", target_id=user.id, note=f"Changed from {old_role} to {new_role}. {reason}", details=_audit_actor_details(admin))
    db.add(audit)
    db.commit()
    if background_tasks:
        background_tasks.add_task(_notify_user, user.phone_number, user.full_name, "ROLE_CHANGED", f"Role changed from {old_role.value} to {new_role.value}. {reason}")
    return {"status": "Role updated", "new_role": new_role}

@router.post("/enroll", response_model=UserResponse)
def enroll_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Manually enroll a user into the platform governor."""
    from app.services.auth_service import register_user
    existing = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Identity already registered")
    return register_user(db, payload)

@router.delete("/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.models.user import UserStatus
    from app.services.session_service import revoke_all_user_sessions

    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, "DELETED", reason)
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="USER_SOFT_DELETE", target_type="USER", target_id=user_id, note=reason, details=_audit_actor_details(admin))
    db.add(audit)
    user.phone_number = f"DEL{str(uuid.uuid4()).replace('-', '')[:12]}"
    user.full_name = "DELETED_USER"
    user.email = None
    user.national_id = None
    user.id_document_url = None
    user.password_hash = "disabled"
    user.ussd_pin_hash = None
    user.status = UserStatus.CLOSED
    user.is_active = False
    user.is_suspended = True
    user.status_notes = reason
    db.commit()
    import asyncio

    try:
        asyncio.run(revoke_all_user_sessions(db, user.id, reason="admin_soft_delete"))
    except RuntimeError:
        pass
    return {"status": "User closed and anonymized", "user_id": str(user_id)}

@router.post("/{user_id}/verify")
def verify_user_identity(
    user_id: uuid.UUID,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.id_verified = True
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="USER_VERIFY", target_type="USER", target_id=user.id, note=reason, details=_audit_actor_details(admin))
    db.add(audit)
    db.commit()
    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, "VERIFIED", reason)
    return {"message": "Identity Verified"}

@router.post("/{user_id}/status")
def update_user_status(
    user_id: uuid.UUID,
    target_status: str,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.models.user import UserStatus

    normalized = target_status.lower()
    try:
        user.status = UserStatus(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user status") from exc
    user.is_suspended = (target_status.upper() in ["SUSPENDED", "CLOSED", "FLAGGED"])
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="USER_STATUS_UPDATE", target_type="USER", target_id=user.id, note=reason, details={**_audit_actor_details(admin), "new_status": target_status})
    db.add(audit)
    db.commit()
    # Map status to notification key
    notif_key = target_status.upper() if target_status.upper() in ("SUSPENDED", "ACTIVE", "FLAGGED", "CLOSED") else "ACTIVE"
    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, notif_key, reason)
    return {"message": "User status adjusted", "audit_ref": str(audit.id)}

@router.post("/{user_id}/reinstate")
def reinstate_user(
    user_id: uuid.UUID,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.models.user import UserStatus

    user.status = UserStatus.ACTIVE
    user.is_suspended = False
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="USER_REINSTATE", target_type="USER", target_id=user.id, note=reason, details=_audit_actor_details(admin))
    db.add(audit)
    db.commit()
    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, "ACTIVE", reason)
    return {"status": "User reinstated to active duty"}

@router.post("/{user_id}/trust")
def adjust_trust_score(
    user_id: uuid.UUID,
    adjustment: float,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.trust_score = max(0, min(100, user.trust_score + adjustment))
    audit = SystemAudit(admin_id=_audit_admin_id(admin), action="TRUST_SCORE_ADJUST", target_type="USER", target_id=user.id, note=reason, details={**_audit_actor_details(admin), "adjustment": adjustment})
    db.add(audit)
    db.commit()
    notif_key = "TRUST_UP" if adjustment >= 0 else "TRUST_DOWN"
    background_tasks.add_task(_notify_user, user.phone_number, user.full_name, notif_key, reason)
    return {"new_score": user.trust_score}
