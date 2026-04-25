import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles, check_lockdown
from app.models.listing import Listing, ListingStatus, Offer
from app.models.user import User, UserRole
from app.schemas.listing import (
    CounterOfferRequest,
    ListingCreate,
    ListingResponse,
    ListingSearchResponse,
    PaginationMeta,
    OfferCreate,
    OfferResponse,
)
from app.schemas.transaction import OrderResponse
from app.services.marketplace_service import marketplace_core

router = APIRouter()


@router.post("", response_model=ListingResponse)
@router.post("/", response_model=ListingResponse, include_in_schema=False)
def create_market_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown)
) -> Listing:
    return marketplace_core.create_listing(db, seller, payload)


@router.get("/search", response_model=ListingSearchResponse)
def search_market_listings(
    db: Session = Depends(get_db),
    crop: str | None = Query(default=None, min_length=1, max_length=50),
    location: str | None = Query(default=None, min_length=1, max_length=200),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    grade: str | None = Query(default=None, min_length=1, max_length=20),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ListingSearchResponse:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price")

    listings, total = marketplace_core.search_listings(
        db=db,
        crop=crop,
        location=location,
        min_price=min_price,
        max_price=max_price,
        grade=grade,
        limit=limit,
        offset=offset,
    )

    return ListingSearchResponse(
        success=True,
        data=listings,
        pagination=PaginationMeta(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + len(listings)) < total,
        ),
    )


@router.get("", response_model=list[ListingResponse])
@router.get("/", response_model=list[ListingResponse], include_in_schema=False)
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
    lockdown: bool = Depends(check_lockdown)
) -> Offer:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return marketplace_core.create_offer(db, current_user, listing, payload)


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
    lockdown: bool = Depends(check_lockdown)
):
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.seller_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return marketplace_core.accept_offer(db, listing, offer)


@router.post("/{listing_id}/offers/{offer_id}/reject", response_model=OfferResponse)
def reject_listing_offer(
    listing_id: uuid.UUID,
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown)
) -> Offer:
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.seller_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing.id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return marketplace_core.reject_offer(db, offer)


@router.post("/{listing_id}/offers/{offer_id}/counter", response_model=OfferResponse)
def counter_listing_offer(
    listing_id: uuid.UUID,
    offer_id: uuid.UUID,
    payload: CounterOfferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown)
) -> Offer:
    """
    AgriTrust Spec: Negotiation Lifecycle.
    """
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Check if user is seller or buyer to allow counter
    if current_user.id not in {offer.buyer_id, offer.seller_id}:
        raise HTTPException(status_code=403, detail="Forbidden")

    return marketplace_core.counter_offer(db, offer, payload.counter_price, current_user)
