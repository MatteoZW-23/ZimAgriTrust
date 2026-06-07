"""Input marketplace service - full implementation.

Implements input marketplace functions for agricultural inputs (seeds, fertilizers, etc.).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.models.input_marketplace import (
    InputCategory,
    InputListing,
    InputOffer,
    InputListingStatus,
    InputOfferStatus,
    InputOrder,
    InputOrderStatus,
    InputPriceAlert,
    InputReport,
    InputReportReason,
    InputReportStatus,
)
from app.models.user import User

logger = logging.getLogger(__name__)


# Categories
def list_categories(db: Session, active_only: bool = True) -> List[InputCategory]:
    """List all input categories."""
    query = db.query(InputCategory)
    if active_only:
        query = query.filter(InputCategory.is_active == True)
    return query.order_by(InputCategory.name).all()


def upsert_category(
    db: Session,
    slug: str,
    name: str,
    description: Optional[str] = None,
    requires_registration: bool = False,
    requires_expiry: bool = False,
    requires_agent_verification: bool = False,
    is_regulated: bool = False,
    is_active: bool = True,
) -> InputCategory:
    """Create or update an input category."""
    category = db.query(InputCategory).filter(InputCategory.slug == slug).first()
    
    if category:
        category.name = name
        category.description = description
        category.requires_registration = requires_registration
        category.requires_expiry = requires_expiry
        category.requires_agent_verification = requires_agent_verification
        category.is_regulated = is_regulated
        category.is_active = is_active
        category.updated_at = datetime.now(timezone.utc)
    else:
        category = InputCategory(
            slug=slug,
            name=name,
            description=description,
            requires_registration=requires_registration,
            requires_expiry=requires_expiry,
            requires_agent_verification=requires_agent_verification,
            is_regulated=is_regulated,
            is_active=is_active,
        )
        db.add(category)
    
    db.commit()
    db.refresh(category)
    return category


# Listings
def create_listing(
    db: Session,
    seller: User,
    category_id: uuid.UUID,
    product_name: str,
    description: str,
    quantity: float,
    unit: str,
    price_per_unit: float,
    **kwargs
) -> InputListing:
    """Create a new input listing."""
    listing = InputListing(
        seller_id=seller.id,
        category_id=category_id,
        product_name=product_name,
        description=description,
        quantity=quantity,
        unit=unit,
        price_per_unit=price_per_unit,
        **kwargs
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def update_listing(
    db: Session,
    listing_id: uuid.UUID,
    seller: User,
    **updates
) -> Optional[InputListing]:
    """Update an input listing."""
    listing = db.query(InputListing).filter(
        InputListing.id == listing_id,
        InputListing.seller_id == seller.id
    ).first()
    
    if not listing:
        return None
    
    for key, value in updates.items():
        if hasattr(listing, key):
            setattr(listing, key, value)
    
    listing.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing(db: Session, listing_id: uuid.UUID) -> Optional[InputListing]:
    """Get a single input listing by ID."""
    return db.query(InputListing).filter(InputListing.id == listing_id).first()


def search_listings(
    db: Session,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    verified_only: bool = False,
    province: Optional[str] = None,
    seller_id: Optional[uuid.UUID] = None,
    include_expired: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> List[InputListing]:
    """Search input listings with filters used by the API endpoint."""
    query = db.query(InputListing)

    if not include_expired:
        query = query.filter(cast(InputListing.status, String) != InputListingStatus.removed.value)

    if q:
        term = f"%{q.strip()}%"
        if term != "%%":
            query = query.filter(
                or_(
                    InputListing.product_name.ilike(term),
                    InputListing.brand.ilike(term),
                    InputListing.description.ilike(term),
                )
            )

    if category_id:
        query = query.filter(InputListing.category_id == category_id)

    if brand:
        query = query.filter(InputListing.brand.ilike(f"%{brand.strip()}%"))

    if province:
        query = query.filter(InputListing.province.ilike(f"%{province.strip()}%"))

    if seller_id:
        query = query.filter(InputListing.seller_id == seller_id)

    if min_price is not None:
        query = query.filter(InputListing.price_per_unit >= min_price)

    if max_price is not None:
        query = query.filter(InputListing.price_per_unit <= max_price)

    if verified_only:
        query = query.filter(InputListing.verified_at.isnot(None))

    return query.order_by(InputListing.created_at.desc()).offset(offset).limit(limit).all()


def list_listings(
    db: Session,
    category_id: Optional[int] = None,
    location_district: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    active_only: bool = True,
    limit: int = 100,
) -> List[InputListing]:
    """Backward-compatible listing helper."""
    return search_listings(
        db,
        category_id=category_id,
        province=location_district,
        min_price=min_price,
        max_price=max_price,
        include_expired=not active_only,
        limit=limit,
    )


# Offers
def create_offer(
    db: Session,
    buyer: User,
    listing_id: uuid.UUID,
    offered_price_per_unit: float,
    quantity: float,
    message: Optional[str] = None,
    note: Optional[str] = None,
) -> InputOffer:
    """Create an offer on an input listing."""
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Input listing not found")
    offer = InputOffer(
        buyer_id=buyer.id,
        listing_id=listing_id,
        offered_price_per_unit=offered_price_per_unit,
        quantity=quantity,
        total_amount=round(float(offered_price_per_unit) * float(quantity), 2),
        currency=listing.currency,
        note=note if note is not None else message,
        status="pending",
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def decide_offer(
    db: Session,
    offer_id: uuid.UUID,
    seller: User,
    accept: bool,
    counter_price: Optional[float] = None,
) -> Optional[InputOffer]:
    """Accept or reject an offer."""
    offer = db.query(InputOffer).filter(
        InputOffer.id == offer_id,
        InputOffer.listing.has(InputListing.seller_id == seller.id)
    ).first()
    
    if not offer:
        return None
    
    offer.status = "accepted" if accept else "rejected"
    offer.decided_at = datetime.now(timezone.utc)
    
    if accept and counter_price:
        offer.final_price_per_unit = counter_price
    
    db.commit()
    db.refresh(offer)
    return offer


# Orders
def create_order(
    db: Session,
    buyer: User,
    offer_id: uuid.UUID,
    shipping_address: str,
) -> InputOrder:
    """Create an order from an accepted offer."""
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id).first()
    
    if not offer or offer.status != "accepted":
        raise ValueError("Offer must be accepted before creating order")
    
    order = InputOrder(
        buyer_id=buyer.id,
        offer_id=offer_id,
        seller_id=offer.listing.seller_id,
        shipping_address=shipping_address,
        status="pending_payment",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def accept_offer(
    db: Session,
    seller: User,
    offer_id: uuid.UUID,
    delivery_address: Optional[str] = None,
) -> InputOrder:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id).first()
    listing = db.query(InputListing).filter(InputListing.id == offer.listing_id).first() if offer else None
    if not offer or not listing or listing.seller_id != seller.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Offer not found")
    if str(offer.status) not in {"pending", "InputOfferStatus.pending"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Offer is not pending")

    subtotal = round(float(offer.total_amount), 2)
    platform_fee = round(subtotal * 0.05, 2)
    escrow_fee = 0.0
    total = round(subtotal + escrow_fee, 2)
    seller_payout = round(subtotal - platform_fee, 2)

    offer.status = InputOfferStatus.accepted
    offer.decided_at = datetime.now(timezone.utc)
    order = InputOrder(
        offer_id=offer.id,
        listing_id=offer.listing_id,
        seller_id=listing.seller_id,
        buyer_id=offer.buyer_id,
        order_number=f"INP-{uuid.uuid4().hex[:8].upper()}",
        quantity=offer.quantity,
        unit_price=offer.offered_price_per_unit,
        subtotal=subtotal,
        platform_fee=platform_fee,
        escrow_fee=escrow_fee,
        total_amount=total,
        seller_payout=seller_payout,
        currency=offer.currency,
        status=InputOrderStatus.pending,
        delivery_address=delivery_address,
    )
    db.add(order)
    db.flush()
    return order


def reject_offer(
    db: Session,
    seller: User,
    offer_id: uuid.UUID,
    reason: Optional[str] = None,
) -> InputOffer:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id).first()
    listing = db.query(InputListing).filter(InputListing.id == offer.listing_id).first() if offer else None
    if not offer or not listing or listing.seller_id != seller.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Offer not found")
    offer.status = InputOfferStatus.rejected
    offer.decided_at = datetime.now(timezone.utc)
    offer.decision_notes = reason
    return offer


def withdraw_offer(db: Session, buyer: User, offer_id: uuid.UUID) -> InputOffer:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id, InputOffer.buyer_id == buyer.id).first()
    if not offer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Offer not found")
    offer.status = InputOfferStatus.withdrawn
    offer.decided_at = datetime.now(timezone.utc)
    return offer


def mark_shipped(
    db: Session,
    seller: User,
    order_id: uuid.UUID,
    tracking_number: Optional[str] = None,
) -> InputOrder:
    order = db.query(InputOrder).filter(InputOrder.id == order_id, InputOrder.seller_id == seller.id).first()
    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = InputOrderStatus.shipped
    order.tracking_number = tracking_number
    order.shipped_at = datetime.now(timezone.utc)
    return order


def confirm_delivery(
    db: Session,
    buyer: User,
    order_id: uuid.UUID,
    rating: Optional[int] = None,
    review: Optional[str] = None,
) -> InputOrder:
    order = db.query(InputOrder).filter(InputOrder.id == order_id, InputOrder.buyer_id == buyer.id).first()
    if not order:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = InputOrderStatus.completed
    order.delivered_at = order.delivered_at or datetime.now(timezone.utc)
    order.confirmed_at = datetime.now(timezone.utc)
    order.review_rating = rating
    order.review_text = review
    return order


def confirm_order_shipment(
    db: Session,
    order_id: uuid.UUID,
    seller: User,
    tracking_number: Optional[str] = None,
) -> Optional[InputOrder]:
    """Confirm order shipment."""
    order = db.query(InputOrder).filter(
        InputOrder.id == order_id,
        InputOrder.seller_id == seller.id
    ).first()
    
    if not order:
        return None
    
    order.status = "shipped"
    order.shipped_at = datetime.now(timezone.utc)
    order.tracking_number = tracking_number
    db.commit()
    db.refresh(order)
    return order


# Price alerts
def create_price_alert(
    db: Session,
    user: User,
    category_id: uuid.UUID,
    target_price: float,
) -> InputPriceAlert:
    """Create a price alert for a category."""
    alert = InputPriceAlert(
        user_id=user.id,
        category_id=category_id,
        target_price=target_price,
        is_active=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# Reports
def create_report(
    db: Session,
    reporter: User,
    listing_id: uuid.UUID,
    reason: InputReportReason,
    description: str,
) -> InputReport:
    """Report a listing for violation."""
    report = InputReport(
        reporter_id=reporter.id,
        listing_id=listing_id,
    reason=reason,
    description=description,
    status=InputReportStatus.PENDING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def resolve_report(
    db: Session,
    report_id: uuid.UUID,
    actor: User,
    decision: str,
    notes: Optional[str] = None,
) -> Optional[InputReport]:
    """Resolve a report."""
    report = db.query(InputReport).filter(InputReport.id == report_id).first()
    
    if not report:
        return None
    
    report.status = InputReportStatus.RESOLVED
    report.resolved_by = actor.id
    report.resolved_at = datetime.now(timezone.utc)
    report.resolution = decision
    report.resolution_notes = notes
    
    db.commit()
    db.refresh(report)
    return report
