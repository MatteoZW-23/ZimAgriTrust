import math
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.listing import Listing, ListingStatus, Offer, OfferStatus
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User
from app.schemas.listing import ListingCreate, OfferCreate
from app.core.policy import calculate_seller_settlement
from app.services.intelligence_service import intelligence_service


# ALGORITHM: Geospatial Proximity Matching (Euclidean Approximation)
def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple distance algorithm for rural logistics matching."""
    if not all([lat1, lon1, lat2, lon2]): return 999.0
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


def suggest_best_matches(db: Session, buyer: User, product: str, limit: int = 5):
    """
    MATCHMAKING ALGORITHM: Multi-objective Optimization.
    Ranks sellers based on: (1) Distance, (2) Price, (3) Producer Trust Score.
    """
    listings = db.query(Listing).filter(
        Listing.status == ListingStatus.ACTIVE,
        Listing.product_type == product
    ).all()
    
    ranked = []
    for l in listings:
        dist = calculate_distance(buyer.latitude, buyer.longitude, l.latitude, l.longitude)
        
        # Scoring Optimization Algorithm: lower is better
        # Normalizes Price, Distance, and Trust into a single feasibility score
        score = (l.price_per_unit * 0.5) + (dist * 10.0) - (l.seller.trust_score * 0.1)
        ranked.append({"listing": l, "feasibility_score": score, "km_est": round(dist * 111, 1)})
        
    return sorted(ranked, key=lambda x: x["feasibility_score"])[:limit]


def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
    if not seller.is_active or seller.is_suspended:
        raise HTTPException(status_code=403, detail="Account restricted")
    
    if not seller.id_verified:
        # Require ID verification for new listings to ensure trust
        raise HTTPException(status_code=403, detail="Identity Verification Required. Please upload National ID.")

    listing = Listing(
        seller_id=seller.id,
        **payload.model_dump()
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Listing not active")
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot bid on own listing")

    offer = Offer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        **payload.model_dump()
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def accept_offer(db: Session, listing: Listing, offer: Offer) -> Order:
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Offer already processed")

    # Update states
    offer.status = OfferStatus.ACCEPTED
    listing.status = ListingStatus.SOLD
    
    # Reject other offers
    db.query(Offer).filter(
        Offer.listing_id == listing.id,
        Offer.id != offer.id
    ).update({"status": OfferStatus.DECLINED})

    # Determine Rural Remoteness for Fee Offsets (Enforced via GPS)
    REMOTE_RURAL_DISTRICTS = ["Binga", "Mudzi", "Mwenezi", "Chiredzi Rural", "Kariba Rural", "Lupane", "Nkayi"]
    is_rural = False
    seller = db.query(User).filter(User.id == offer.seller_id).first()
    
    # DISCOUNT ELIGIBILITY: Must be in a remote district AND be GPS-verified
    if seller and seller.district in REMOTE_RURAL_DISTRICTS:
        if listing.is_location_verified:
            is_rural = True
        else:
            # Audit Point: Potential 'Subsidy Fraud'
            intelligence_service.log_audit_event(db, {
                "type": "LOCATION_INTEGRITY_MISMATCH",
                "user_id": str(seller.id),
                "severity": "MEDIUM",
                "details": f"User claimed rural district '{seller.district}' but listing was not GPS-verified."
            })
        
    total_amount = offer.quantity * offer.offered_price
    platform_fee, seller_payout = calculate_seller_settlement(
        total_amount, 
        seller.trust_score if seller else 0,
        is_rural=is_rural,
        currency=offer.currency
    )

    order = Order(
        offer_id=offer.id,
        listing_id=listing.id,
        buyer_id=offer.buyer_id,
        seller_id=offer.seller_id,
        order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        quantity=offer.quantity,
        total_amount=total_amount,
        platform_fee=platform_fee,
        seller_payout=seller_payout,
        currency=offer.currency,
        status=OrderStatus.PENDING
    )
    db.add(order)
    
    # Simulate immediate escrow hold (Escrow Service logic)
    order.status = OrderStatus.ESCROW_HELD
    
    # Create transaction record for buyer
    txn = Transaction(
        order_id=order.id,
        user_id=order.buyer_id,
        type=TransactionType.ESCROW_HOLD,
        amount=total_amount,
        currency=order.currency,
        status="completed"
    )
    db.add(txn)
    
    db.commit()
    db.refresh(order)
    return order


def reject_offer(db: Session, offer: Offer) -> Offer:
    offer.status = OfferStatus.DECLINED
    db.commit()
    db.refresh(offer)
    return offer
