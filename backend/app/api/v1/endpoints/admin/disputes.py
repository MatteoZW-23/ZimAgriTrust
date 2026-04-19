import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.dispute import Dispute, DisputeStatus
from app.models.system_audit import SystemAudit
from app.schemas.dispute import DisputeResponse

router = APIRouter()

@router.get("", response_model=list[DisputeResponse])
def list_all_disputes(
    db: Session = Depends(get_db),
    status: str = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 105: View all disputes.
    """
    query = db.query(Dispute).options(joinedload(Dispute.order), joinedload(Dispute.raised_by))
    if status:
        query = query.filter(Dispute.status == status.lower())
    return query.all()

@router.post("/{dispute_id}/override")
def admin_override_dispute(
    dispute_id: uuid.UUID,
    resolution_type: str, # REFUND, PAY_FARMER, PARTIAL
    memo: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 114: Override decision.
    Admin makes final binding decision regardless of current state.
    """
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
        
    order = dispute.order
    if not order:
        raise HTTPException(status_code=400, detail="No associated order for this dispute")

    if resolution_type.upper() == "REFUND":
        order.status = "REFUNDED"
    elif resolution_type.upper() == "PAY_FARMER":
        order.status = "COMPLETED"
    
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution_note = f"ADMIN_OVERRIDE: {memo}"
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="DISPUTE_ADMIN_OVERRIDE",
        target_type="DISPUTE",
        target_id=dispute.id,
        note=memo
    )
    db.add(audit)
    db.commit()
    return {"status": "Dispute resolved by Admin Override", "audit_ref": str(audit.id)}
