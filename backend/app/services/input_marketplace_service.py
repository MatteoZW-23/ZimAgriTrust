"""Input marketplace service - full implementation.

Implements input marketplace functions for agricultural inputs (seeds, fertilizers, etc.).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.input_marketplace import (
    InputCategory,
    InputListing,
    InputOffer,
    InputOrder,
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


def list_listings(
    db: Session,
    category_id: Optional[uuid.UUID] = None,
    location_district: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    active_only: bool = True,
    limit: int = 100,
) -> List[InputListing]:
    """List input listings with filters."""
    query = db.query(InputListing)
    
    if active_only:
        query = query.filter(InputListing.is_active == True)
    
    if category_id:
        query = query.filter(InputListing.category_id == category_id)
    
    if location_district:
        query = query.filter(InputListing.location_district == location_district)
    
    if min_price:
        query = query.filter(InputListing.price_per_unit >= min_price)
    
    if max_price:
        query = query.filter(InputListing.price_per_unit <= max_price)
    
    return query.order_by(InputListing.created_at.desc()).limit(limit).all()


# Offers
def create_offer(
    db: Session,
    buyer: User,
    listing_id: uuid.UUID,
    offered_price_per_unit: float,
    quantity: float,
    message: Optional[str] = None,
) -> InputOffer:
    """Create an offer on an input listing."""
    offer = InputOffer(
        buyer_id=buyer.id,
        listing_id=listing_id,
        offered_price_per_unit=offered_price_per_unit,
        quantity=quantity,
        message=message,
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
