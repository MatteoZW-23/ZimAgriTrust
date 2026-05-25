import uuid
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles, check_lockdown, get_current_user
from app.models.listing import Listing, ListingStatus, Offer, OfferStatus
from app.models.listing_extras import (
    ListingReport,
    ListingReportReason,
    ListingReportStatus,
    SavedListing,
)
from app.models.user import User, UserRole
from app.schemas.listing import (
    CounterOfferRequest,
    ListingBoostRequest,
    ListingBoostResponse,
    ListingCreate,
    ListingPhotosResponse,
    ListingPhotosUpdate,
    ListingReportCreate,
    ListingReportResponse,
    ListingResponse,
    ListingSearchResponse,
    ListingStatsResponse,
    ListingUpdate,
    OfferCreate,
    OfferResponse,
    PaginationMeta,
    SavedListingResponse,
)
from app.schemas.transaction import OrderResponse
from app.services.marketplace_service import marketplace_core

router = APIRouter()
logger = logging.getLogger(__name__)

# Boost pricing (F#57). $2 per 7-day cycle, prorated by duration.
BOOST_FEE_PER_DAY_USD = 2.0 / 7.0


@router.post("", response_model=ListingResponse)
@router.post("/", response_model=ListingResponse, include_in_schema=False)
def create_market_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown)
) -> Listing:
    try:
        return marketplace_core.create_listing(db, seller, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create listing")


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
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search listings error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search listings")


@router.get("", response_model=list[ListingResponse])
@router.get("/", response_model=list[ListingResponse], include_in_schema=False)
def list_market_listings(db: Session = Depends(get_db)) -> list[Listing]:
    try:
        return (
            db.query(Listing)
            .filter(Listing.status == ListingStatus.ACTIVE)
            .all()
        )
    except Exception as e:
        logger.error(f"List listings error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve listings")


@router.get("/my", response_model=list[ListingResponse])
@router.get("/me", response_model=list[ListingResponse], include_in_schema=False)
def my_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
) -> list[Listing]:
    try:
        return db.query(Listing).filter(Listing.seller_id == current_user.id).all()
    except Exception as e:
        logger.error(f"My listings error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve listings")


@router.post("/{listing_id}/offers", response_model=OfferResponse)
def place_offer(
    listing_id: uuid.UUID,
    payload: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown)
) -> Offer:
    try:
        return marketplace_core.place_offer(db, listing_id, current_user, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Place offer error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to place offer")


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
    ZimAgritrust Spec: Negotiation Lifecycle.
    """
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.listing_id == listing_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Check if user is seller or buyer to allow counter
    if current_user.id not in {offer.buyer_id, offer.seller_id}:
        raise HTTPException(status_code=403, detail="Forbidden")

    return marketplace_core.counter_offer(db, offer, payload.counter_price, current_user)


# ===========================================================================
# Listing CRUD extras (F#52, F#53, F#54, F#56, F#57, F#58, F#89, F#92, F#94)
# ===========================================================================

def _get_owned_listing(db: Session, listing_id: uuid.UUID, user: User) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You do not own this listing")
    return listing


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing_details(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Listing:
    """F#89 — view listing details. Increments view_count for stats (F#56)."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status == ListingStatus.DELETED:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.view_count = (listing.view_count or 0) + 1
    db.commit()
    db.refresh(listing)
    return listing


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: uuid.UUID,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
    lockdown: bool = Depends(check_lockdown),
) -> Listing:
    """F#53 — edit listing."""
    listing = _get_owned_listing(db, listing_id, current_user)
    if listing.status not in (ListingStatus.ACTIVE, ListingStatus.PENDING):
        raise HTTPException(status_code=400, detail=f"Cannot edit listing in status {listing.status.value}")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(listing, field, value)
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", response_model=ListingResponse)
def delete_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
    lockdown: bool = Depends(check_lockdown),
) -> Listing:
    """F#54 — delete listing (soft delete)."""
    listing = _get_owned_listing(db, listing_id, current_user)
    # Disallow delete if there are accepted offers / pending orders
    has_active_orders = db.query(Offer).filter(
        Offer.listing_id == listing.id,
        Offer.status == OfferStatus.ACCEPTED,
    ).count() > 0
    if has_active_orders:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete listing with accepted offers; cancel orders first.",
        )
    listing.status = ListingStatus.DELETED
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return listing


@router.post("/{listing_id}/expire", response_model=ListingResponse)
def expire_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
    lockdown: bool = Depends(check_lockdown),
) -> Listing:
    """F#58 — mark listing as expired."""
    listing = _get_owned_listing(db, listing_id, current_user)
    listing.status = ListingStatus.EXPIRED
    listing.expires_at = datetime.now(timezone.utc)
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return listing


# --- Photos (F#52) ---------------------------------------------------------
@router.post("/{listing_id}/photos", response_model=ListingPhotosResponse)
def add_listing_photos(
    listing_id: uuid.UUID,
    payload: ListingPhotosUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
    lockdown: bool = Depends(check_lockdown),
) -> ListingPhotosResponse:
    """F#52 — add photo URLs to a listing. Photo upload itself is handled by media_service."""
    listing = _get_owned_listing(db, listing_id, current_user)
    existing = list(listing.photo_urls or [])
    for url in payload.urls:
        if url and url not in existing:
            existing.append(url)
    listing.photo_urls = existing
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return ListingPhotosResponse(listing_id=listing.id, photo_urls=existing)


@router.delete("/{listing_id}/photos", response_model=ListingPhotosResponse)
def remove_listing_photo(
    listing_id: uuid.UUID,
    url: str = Query(..., description="The photo URL to remove"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
    lockdown: bool = Depends(check_lockdown),
) -> ListingPhotosResponse:
    listing = _get_owned_listing(db, listing_id, current_user)
    existing = [u for u in (listing.photo_urls or []) if u != url]
    listing.photo_urls = existing
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return ListingPhotosResponse(listing_id=listing.id, photo_urls=existing)


# --- Boost (F#57) ----------------------------------------------------------
@router.post("/{listing_id}/boost", response_model=ListingBoostResponse)
def boost_listing(
    listing_id: uuid.UUID,
    payload: ListingBoostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER)),
    lockdown: bool = Depends(check_lockdown),
) -> ListingBoostResponse:
    """F#57 — pay $2 (per 7 days) to boost a listing's visibility.

    Fee is deducted from the user's wallet balance. No external payment
    intent is created in this MVP — buyer must have sufficient wallet funds.
    """
    listing = _get_owned_listing(db, listing_id, current_user)
    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active listings can be boosted")

    fee = round(BOOST_FEE_PER_DAY_USD * payload.duration_days, 2)

    from app.services.wallet_service import wallet_service
    idempotency_key = f"boost:{listing.id}:{payload.duration_days}"
    success = wallet_service.withdraw(
        db,
        user_id=current_user.id,
        amount=fee,
        currency="USD",
        idempotency_key=idempotency_key,
    )
    if not success:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient wallet balance. Boost requires ${fee:.2f}.",
        )

    now = datetime.now(timezone.utc)
    base = listing.boosted_until if (listing.boosted_until and listing.boosted_until > now) else now
    listing.is_boosted = True
    listing.boost_fee = (listing.boost_fee or 0) + fee
    listing.boosted_until = base + timedelta(days=payload.duration_days)
    listing.updated_at = now
    db.commit()
    db.refresh(listing)

    balance_data = wallet_service.get_balance_detail(db, current_user.id)
    return ListingBoostResponse(
        listing_id=listing.id,
        is_boosted=listing.is_boosted,
        boosted_until=listing.boosted_until,
        boost_fee=listing.boost_fee,
        wallet_balance=balance_data.get("available", 0.0),
    )


# --- Stats (F#56) ----------------------------------------------------------
@router.get("/{listing_id}/stats", response_model=ListingStatsResponse)
def get_listing_stats(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.FARMER, UserRole.BUYER, UserRole.ADMIN)),
) -> ListingStatsResponse:
    listing = _get_owned_listing(db, listing_id, current_user)
    offer_count = db.query(func.count(Offer.id)).filter(Offer.listing_id == listing.id).scalar() or 0
    accepted_count = (
        db.query(func.count(Offer.id))
        .filter(Offer.listing_id == listing.id, Offer.status == OfferStatus.ACCEPTED)
        .scalar()
    ) or 0
    created_at_aware = listing.created_at.replace(tzinfo=timezone.utc) if listing.created_at.tzinfo is None else listing.created_at
    days_active = (datetime.now(timezone.utc) - created_at_aware).days
    return ListingStatsResponse(
        listing_id=listing.id,
        view_count=listing.view_count or 0,
        offer_count=int(offer_count),
        accepted_offer_count=int(accepted_count),
        days_active=max(0, days_active),
        is_boosted=bool(listing.is_boosted),
    )


# --- Save / favorite (F#92) ------------------------------------------------
@router.post("/{listing_id}/save", response_model=SavedListingResponse, status_code=status.HTTP_201_CREATED)
def save_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedListing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    existing = (
        db.query(SavedListing)
        .filter(SavedListing.user_id == current_user.id, SavedListing.listing_id == listing_id)
        .first()
    )
    if existing:
        return existing
    saved = SavedListing(user_id=current_user.id, listing_id=listing_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.delete("/{listing_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(SavedListing).filter(
        SavedListing.user_id == current_user.id,
        SavedListing.listing_id == listing_id,
    ).delete()
    db.commit()
    return None


@router.get("/my/saved", response_model=list[SavedListingResponse])
@router.get("/me/saved", response_model=list[SavedListingResponse], include_in_schema=False)
def list_saved_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SavedListing]:
    return (
        db.query(SavedListing)
        .filter(SavedListing.user_id == current_user.id)
        .order_by(SavedListing.created_at.desc())
        .all()
    )


# --- Report listing (F#94) -------------------------------------------------
@router.post("/{listing_id}/report", response_model=ListingReportResponse, status_code=status.HTTP_201_CREATED)
def report_listing(
    listing_id: uuid.UUID,
    payload: ListingReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingReport:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot report your own listing")

    try:
        reason_enum = ListingReportReason(payload.reason.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason. Allowed: {[r.value for r in ListingReportReason]}",
        )

    report = ListingReport(
        listing_id=listing_id,
        reporter_id=current_user.id,
        reason=reason_enum,
        details=payload.details,
        status=ListingReportStatus.OPEN,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
