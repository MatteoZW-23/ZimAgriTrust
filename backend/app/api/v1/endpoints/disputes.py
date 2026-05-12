import uuid
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.api.v1.dependencies import get_create_dispute, get_resolve_dispute_use_case
from app.application.disputes.dto import CreateDisputeCommand, ResolveDisputeCommand
from app.models.dispute import Dispute
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
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> list[Dispute]:
    return db.query(Dispute).all()


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
