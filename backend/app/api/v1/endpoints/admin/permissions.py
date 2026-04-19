from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.system_audit import SystemAudit

router = APIRouter()

@router.get("/roles")
def list_available_roles(
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 250: View all system roles and their inherent base scopes.
    """
    return [
        {"role": UserRole.ADMIN, "scopes": ["full_access", "audit_view", "system_config"]},
        {"role": UserRole.AGENT, "scopes": ["verification", "dispute_mediate", "user_view"]},
        {"role": UserRole.FARMER, "scopes": ["list_crops", "accept_offers", "ussd_access"]},
        {"role": UserRole.BUYER, "scopes": ["browse_marketplace", "make_offers", "ecocash_pay"]}
    ]

@router.post("/roles/audit")
def audit_role_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 258: Role audit report.
    """
    from sqlalchemy import func
    stats = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    return [{"role": r[0], "count": r[1]} for r in stats]

@router.patch("/users/{user_id}/permissions")
def grant_custom_scope(
    user_id: str,
    scope: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 256: Grant specific permission to user.
    Simulated as metadata update.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # In a real dynamic RBAC, we'd update a join table.
    # Here we log it as an intent.
    audit = SystemAudit(
        admin_id=admin.id,
        action="PERMISSION_GRANT",
        target_type="USER",
        target_id=user.id,
        note=f"Granted scope: {scope}"
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "user": user.full_name, "granted": scope}
