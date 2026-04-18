import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.listing import Listing, ListingStatus, Offer
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreate, ListingResponse, OfferCreate, OfferResponse
# Use OrderResponse from transaction schema
from app.schemas.transaction import OrderResponse
from app.services.marketplace_service import accept_offer, create_listing, create_offer, reject_offer

router = APIRouter()


@router.post("/", response_model=ListingResponse)
def create_market_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> Listing:

    return create_listing(db, seller, payload)


@router.get("/", response_model=list[ListingResponse])
def list_market_listings(db: Session = Depends(get_db)) -> list[Listing]:
    return (
        db.query(Listing)
        .filter(Listing.status == ListingStatus.ACTIVE)
        .all()
    )


@router.get("/me", response_model=list[ListingResponse])
def my_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> list[Listing]:
    return db.query(Listing).filter(Listing.seller_id == current_user.id).all()


@router.post("/{listing_id}/offers", response_model=OfferResponse)
def place_offer(
    listing_id: uuid.UUID,
    payload: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> Offer:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return create_offer(db, current_user, listing, payload)


@router.get("/{listing_id}/offers", response_model=list[OfferResponse])
def list_offers_for_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> list[Offer]:
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.seller_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return db.query(Offer).filter(Offer.listing_id == listing.id).all()


@router.post("/{listing_id}/offers/{offer_id}/accept", response_model=OrderResponse)
def accept_listing_offer(
    listing_id: uuid.UUID,
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
):
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.seller_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return accept_offer(db, listing, offer)


@router.post("/{listing_id}/offers/{offer_id}/reject", response_model=OfferResponse)
def reject_listing_offer(
    listing_id: uuid.UUID,
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> Offer:
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.seller_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return reject_offer(db, offer)
