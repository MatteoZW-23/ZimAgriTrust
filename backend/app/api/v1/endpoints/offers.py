import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.listing import Offer, OfferStatus
from app.models.user import User, UserRole
from app.schemas.listing import CounterOfferRequest, OfferResponse
from app.schemas.transaction import OrderResponse
from app.services.marketplace_service import marketplace_core

router = APIRouter()


@router.get("/received", response_model=list[OfferResponse])
def offers_received(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> list[Offer]:
    return (
        db.query(Offer)
        .filter(Offer.seller_id == current_user.id)
        .order_by(Offer.created_at.desc())
        .all()
    )


@router.get("/made", response_model=list[OfferResponse])
def offers_made(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> list[Offer]:
    return (
        db.query(Offer)
        .filter(Offer.buyer_id == current_user.id)
        .order_by(Offer.created_at.desc())
        .all()
    )


def _load_offer(db: Session, offer_id: uuid.UUID, current_user: User) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if current_user.id not in {offer.buyer_id, offer.seller_id} and current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Access denied")
    return offer


@router.post("/{offer_id}/accept", response_model=OrderResponse)
def accept_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = _load_offer(db, offer_id, current_user)
    if offer.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the listing owner can accept this offer.")
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Offer is already {offer.status}.")
    return marketplace_core.accept_offer(db, offer.listing, offer)


@router.post("/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    offer = _load_offer(db, offer_id, current_user)
    if offer.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the listing owner can reject this offer.")
    return marketplace_core.reject_offer(db, offer)


@router.post("/{offer_id}/counter", response_model=OfferResponse)
def counter_offer(
    offer_id: uuid.UUID,
    payload: CounterOfferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Offer:
    offer = _load_offer(db, offer_id, current_user)
    return marketplace_core.counter_offer(db, offer, payload.counter_price, current_user)
