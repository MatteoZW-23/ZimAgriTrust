import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse, UserRegister
from app.models.system_audit import SystemAudit

router = APIRouter()

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
        admin_id=admin.id,
        action="USER_BULK_VERIFY",
        target_type="BATCH",
        target_id=None,
        note=f"Bulk verified {updated} users"
    )
    db.add(audit)
    db.commit()
    return {"verified_count": updated}

@router.post("/{user_id}/verify-reject")
def reject_verification(
    user_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """
    Function 12: Reject verification.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.id_verified = False # Explicitly mark as not verified
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="VERIFICATION_REJECT",
        target_type="USER",
        target_id=user.id,
        note=reason
    )
    db.add(audit)
    db.commit()
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
        admin_id=admin.id,
        action="USER_PASSWORD_RESET",
        target_type="USER",
        target_id=user.id,
        note="Manual admin override of password"
    )
    db.add(audit)
    db.commit()
    return {"status": "Password changed successfully"}

@router.patch("/{user_id}/role")
def change_user_role(
    user_id: uuid.UUID,
    new_role: UserRole,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 25: Change user role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_role = user.role
    user.role = new_role
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_ROLE_CHANGE",
        target_type="USER",
        target_id=user.id,
        note=f"Changed from {old_role} to {new_role}"
    )
    db.add(audit)
    db.commit()
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
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Purge a user record for security or compliance protocols."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_PURGE",
        target_type="USER",
        target_id=user_id,
        note=reason
    )
    db.add(audit)
    db.delete(user)
    db.commit()
    return {"status": "User wiped from national database"}

@router.post("/{user_id}/verify")
def verify_user_identity(
    user_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Authenticate and verify a user's national identity credentials."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.id_verified = True
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_VERIFY",
        target_type="USER",
        target_id=user.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"message": "Identity Verified"}

@router.post("/{user_id}/status")
def update_user_status(
    user_id: uuid.UUID,
    target_status: str,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = target_status.lower()
    user.is_suspended = (target_status.upper() in ["SUSPENDED", "CLOSED", "FLAGGED"])
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_STATUS_UPDATE",
        target_type="USER",
        target_id=user.id,
        note=reason,
        details={"new_status": target_status}
    )
    db.add(audit)
    db.commit()
    return {"message": "User status adjusted", "audit_ref": str(audit.id)}

@router.post("/{user_id}/reinstate")
def reinstate_user(
    user_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 19: Reinstate user (Remove suspension).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = "active"
    user.is_suspended = False
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_REINSTATE",
        target_type="USER",
        target_id=user.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"status": "User reinstated to active duty"}

@router.post("/{user_id}/trust")
def adjust_trust_score(
    user_id: uuid.UUID,
    adjustment: float,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.trust_score = max(0, min(100, user.trust_score + adjustment))
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="TRUST_SCORE_ADJUST",
        target_type="USER",
        target_id=user.id,
        note=reason,
        details={"adjustment": adjustment}
    )
    db.add(audit)
    db.commit()
    return {"new_score": user.trust_score}
