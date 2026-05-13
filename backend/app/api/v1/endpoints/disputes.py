import uuid
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.api.v1.dependencies import get_create_dispute, get_resolve_dispute_use_case
from app.application.disputes.dto import CreateDisputeCommand, ResolveDisputeCommand
from app.models.dispute import Dispute
from app.models.transaction import Order
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeCreate, DisputeResolve, DisputeResponse, SettlementProposal
from app.services.dispute_service import create_dispute, resolve_dispute, propose_settlement, accept_settlement

router = APIRouter()

_DISPUTE_USE_DOMAIN = os.getenv("DISPUTE_USE_DOMAIN", "false").lower() == "true"


@router.post("", response_model=DisputeResponse)
def raise_dispute(
    payload: DisputeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    create_dispute_uc=Depends(get_create_dispute),
) -> Dispute:
    if _DISPUTE_USE_DOMAIN:
        cmd = CreateDisputeCommand(
            order_id=payload.order_id,
            raised_by=current_user.id,
            dispute_type=payload.type,
            description=payload.description,
        )
        dispute = create_dispute_uc(cmd)
        # Convert domain entity to ORM for response
        return db.query(Dispute).filter(Dispute.id == dispute.id.value).first()
    return create_dispute(db, payload, current_user)


@router.get("", response_model=list[DisputeResponse])
def list_disputes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Dispute]:
    if current_user.role in {UserRole.AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        return db.query(Dispute).all()

    return (
        db.query(Dispute)
        .join(Order, Dispute.order_id == Order.id)
        .filter(
            (Dispute.raised_by == current_user.id)
            | (Order.buyer_id == current_user.id)
            | (Order.seller_id == current_user.id)
        )
        .order_by(Dispute.created_at.desc())
        .all()
    )


@router.post("/{dispute_id}/evidence")
async def upload_evidence(
    dispute_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    order = dispute.order
    is_party = order and current_user.id in {order.buyer_id, order.seller_id}
    if not is_party and current_user.role not in {UserRole.AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Only dispute parties or staff can upload evidence")

    upload_dir = Path("uploads") / "dispute_evidence" / str(dispute_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    for item in files:
        safe_name = f"{uuid.uuid4().hex}_{Path(item.filename or 'evidence.jpg').name}"
        destination = upload_dir / safe_name
        destination.write_bytes(await item.read())
        uploaded.append(f"/uploads/dispute_evidence/{dispute_id}/{safe_name}")

    memo = dispute.agent_resolution_memo or ""
    dispute.agent_resolution_memo = (
        f"{memo}\nEvidence uploaded by {current_user.id}: {', '.join(uploaded)}"
    ).strip()
    db.commit()

    return {"uploaded": uploaded, "count": len(uploaded)}


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
def resolve_case(
    dispute_id: uuid.UUID,
    payload: DisputeResolve,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
    resolve_dispute_uc=Depends(get_resolve_dispute_use_case),
) -> Dispute:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if _DISPUTE_USE_DOMAIN:
        cmd = ResolveDisputeCommand(
            dispute_id=dispute_id,
            resolution=payload.resolution,
            release_to_farmer=payload.release_to_farmer,
        )
        resolve_dispute_uc(cmd)
        db.refresh(dispute)
        return dispute
    return resolve_dispute(db, dispute, payload)


@router.post("/{dispute_id}/propose-settlement", response_model=DisputeResponse)
def propose_adjustment(
    dispute_id: uuid.UUID,
    payload: SettlementProposal,
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> Dispute:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return propose_settlement(db, dispute, payload.discount_percent, payload.memo, agent)


@router.post("/{dispute_id}/accept-settlement", response_model=DisputeResponse)
def approve_terms(
    dispute_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dispute:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return accept_settlement(db, dispute, current_user)
