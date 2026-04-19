import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.listing import Listing, ListingStatus
from app.schemas.admin import ListingReviewResponse
from app.schemas.listing import ListingResponse

router = APIRouter()

@router.get("/review-queue", response_model=list[ListingReviewResponse])
def review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> list[ListingReviewResponse]:
    listings = (
        db.query(Listing)
        .options(joinedload(Listing.seller), joinedload(Listing.offers))
        .filter(Listing.verification_status.in_(["pending", "PENDING"]))
        .order_by(Listing.created_at.desc())
        .all()
    )
    return [
        ListingReviewResponse(
            id=listing.id,
            farmer_id=listing.seller_id,
            farmer_name=listing.seller.full_name if listing.seller else "N/A",
            farmer_phone=listing.seller.phone_number if listing.seller else "N/A",
            product_type=listing.product_type or "Unknown",
            quantity=listing.quantity or 0,
            grade=listing.grade or "N/A",
            location=f"{listing.location_province or 'N/A'}, {listing.location_district or 'N/A'}",
            price_per_unit=listing.price_per_unit or 0.0,
            status=listing.status.value if hasattr(listing.status, 'value') else str(listing.status),
            verification_status=listing.verification_status or "PENDING",
            notes=listing.notes,
            offer_count=len(listing.offers) if listing.offers else 0
        )
        for listing in listings
    ]

@router.post("/{listing_id}/verify", response_model=ListingResponse)
def verify_listing(
    listing_id: uuid.UUID,
    approved: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.verification_status = "APPROVED" if approved else "REJECTED"
    if not approved:
        listing.status = ListingStatus.SUSPENDED
    db.commit()
    db.refresh(listing)
    return listing
