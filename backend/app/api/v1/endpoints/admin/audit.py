from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogOut, AuditChainVerification
from app.services.audit_service import verify_audit_chain

router = APIRouter()


@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    admin_id: Optional[int] = None,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Fetch audit logs with advanced filtering.
    Restricted to Super Admins and System Admins.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
        
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/verify", response_model=AuditChainVerification)
def verify_logs(
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    """
    Run cryptographic verification of the entire audit chain.
    Restricted to Super Admins only.
    """
    return verify_audit_chain(db, limit=limit)
