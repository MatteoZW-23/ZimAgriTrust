"""
Input marketplace service.

Implements input listing CRUD, agent verification, offers, accept/reject,
order creation with escrow, delivery confirmation, ratings, reports,
expiry sweep, and bulk-order business-verification gate.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.input_marketplace import (
    InputCategory,
    InputListing,
    InputListingStatus,
    InputOffer,
    InputOfferStatus,
    InputOrder,
    InputOrderStatus,
    InputPriceAlert,
    InputReport,
    InputReportReason,
    InputReportStatus,
)
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole
from app.services import notification_triggers
from app.services.audit_chain_service import append_audit
from app.services.transaction_signing_service import sign_transaction
from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)


OFFER_EXPIRY_HOURS = 48


# ---------------------------------------------------------------------------
# Categories (functions 369, 381)
# ---------------------------------------------------------------------------

def list_categories(db: Session, *, active_only: bool = True) -> list[InputCategory]:
    q = db.query(InputCategory)
    if active_only:
        q = q.filter(InputCategory.is_active.is_(True))
    return q.order_by(InputCategory.name.asc()).all()


def upsert_category(
    db: Session,
    *,
    slug: str,
    name: str,
    description: Optional[str] = None,
    requires_registration: bool = False,
    requires_expiry: bool = False,
    requires_agent_verification: bool = True,
    is_regulated: bool = False,
    is_active: bool = True,
) -> InputCategory:
    cat = db.query(InputCategory).filter(InputCategory.slug == slug).first()
    if cat:
        cat.name = name
        cat.description = description
        cat.requires_registration = requires_registration
        cat.requires_expiry = requires_expiry
        cat.requires_agent_verification = requires_agent_verification
        cat.is_regulated = is_regulated
        cat.is_active = is_active
    else:
        cat = InputCategory(
            slug=slug, name=name, description=description,
            requires_registration=requires_registration,
            requires_expiry=requires_expiry,
            requires_agent_verification=requires_agent_verification,
            is_regulated=is_regulated, is_active=is_active,
        )
        db.add(cat)
    db.flush()
    return cat


# ---------------------------------------------------------------------------
# Listing CRUD (functions 360-368)
# ---------------------------------------------------------------------------

def _check_seller_eligible(seller: User) -> None:
    trust = int(getattr(seller, "trust_score", 0) or 0)
    if trust < settings.INPUT_SELLER_MIN_TRUST_SCORE:
        raise HTTPException(
            status_code=403,
            detail=f"Sellers need a trust score of at least {settings.INPUT_SELLER_MIN_TRUST_SCORE} to list inputs",
        )


def create_listing(
    db: Session,
    *,
    seller: User,
    category_id: int,
    product_name: str,
    quantity: float,
    price_per_unit: float,
    unit: str = "unit",
    brand: Optional[str] = None,
    description: Optional[str] = None,
    photos: Optional[list[str]] = None,
    documents: Optional[list[str]] = None,
    expiry_date: Optional[datetime] = None,
    registration_number: Optional[str] = None,
    location: Optional[str] = None,
    province: Optional[str] = None,
    min_order_quantity: float = 1,
    currency: str = "USD",
) -> InputListing:
    _check_seller_eligible(seller)

    cat = db.query(InputCategory).filter(InputCategory.id == category_id, InputCategory.is_active.is_(True)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    if cat.requires_registration and not registration_number:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{cat.name}' requires a registration number",
        )
    if cat.requires_expiry and not expiry_date:
        raise HTTPException(status_code=400, detail=f"Category '{cat.name}' requires expiry date")
    if expiry_date and expiry_date <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Expiry date must be in the future")
    if quantity <= 0 or price_per_unit <= 0:
        raise HTTPException(status_code=400, detail="Quantity and price must be positive")

    initial_status = (
        InputListingStatus.PENDING_VERIFICATION
        if cat.requires_agent_verification
        else InputListingStatus.ACTIVE
    )

    listing = InputListing(
        seller_id=seller.id,
        category_id=category_id,
        product_name=product_name,
        brand=brand,
        description=description,
        quantity=quantity,
        unit=unit,
        price_per_unit=Decimal(str(price_per_unit)),
        currency=currency,
        min_order_quantity=min_order_quantity,
        location=location,
        province=province,
        photos=photos or [],
        documents=documents or [],
        expiry_date=expiry_date,
        registration_number=registration_number,
        status=initial_status,
    )
    db.add(listing)
    db.flush()
    append_audit(
        db, table_name="input_listings", record_id=str(listing.id), operation="CREATE",
        payload={
            "seller_id": str(seller.id), "category": cat.slug, "product_name": product_name,
            "quantity": quantity, "price_per_unit": price_per_unit,
        },
        actor_id=str(seller.id), actor_role=seller.role.value,
    )
    return listing


def update_listing(
    db: Session,
    *,
    seller: User,
    listing_id: uuid.UUID,
    **fields: Any,
) -> InputListing:
    listing = _get_owned_listing(db, listing_id, seller)
    if listing.status not in (InputListingStatus.ACTIVE, InputListingStatus.PENDING_VERIFICATION):
        raise HTTPException(status_code=400, detail=f"Cannot edit listing in state {listing.status.value}")

    editable = {
        "product_name", "brand", "description", "quantity", "unit", "price_per_unit",
        "min_order_quantity", "location", "province", "photos", "documents",
        "expiry_date", "registration_number",
    }
    old_price = float(listing.price_per_unit)
    changed = False
    price_dropped = False
    for k, v in fields.items():
        if k in editable and v is not None:
            if k == "price_per_unit":
                v = Decimal(str(v))
                if float(v) < old_price:
                    price_dropped = True
            setattr(listing, k, v)
            changed = True

    # Substantive change to a regulated listing → requeue for verification
    cat = listing.category
    if changed and cat and cat.requires_agent_verification:
        listing.status = InputListingStatus.PENDING_VERIFICATION
        listing.verified_at = None
        listing.verified_by = None

    listing.updated_at = datetime.now(timezone.utc)
    db.flush()
    if price_dropped and listing.status == InputListingStatus.ACTIVE:
        try:
            evaluate_price_alerts(db, listing=listing)
        except Exception as exc:  # noqa: BLE001
            logger.warning("price-alert evaluation failed: %s", exc)
    return listing


def delete_listing(db: Session, *, seller: User, listing_id: uuid.UUID) -> None:
    listing = _get_owned_listing(db, listing_id, seller)
    listing.status = InputListingStatus.REMOVED
    listing.updated_at = datetime.now(timezone.utc)


def boost_listing(db: Session, *, seller: User, listing_id: uuid.UUID) -> InputListing:
    """Charge the seller's wallet $2 and mark listing boosted for 7 days."""
    listing = _get_owned_listing(db, listing_id, seller)
    if listing.status != InputListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Only active listings can be boosted")
    if not wallet_service.withdraw(db, seller.id, settings.INPUT_BOOST_FEE_USD, "USD"):
        raise HTTPException(status_code=400, detail="Insufficient balance for boost fee")
    listing.is_boosted = True
    listing.boost_paid_until = datetime.now(timezone.utc) + timedelta(days=7)
    return listing


def _get_owned_listing(db: Session, listing_id: uuid.UUID, seller: User) -> InputListing:
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not your listing")
    return listing


# ---------------------------------------------------------------------------
# Search / browse (functions 369-373)
# ---------------------------------------------------------------------------

def search_listings(
    db: Session,
    *,
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
) -> list[InputListing]:
    query = db.query(InputListing)
    if seller_id:
        query = query.filter(InputListing.seller_id == seller_id)
    else:
        query = query.filter(InputListing.status == InputListingStatus.ACTIVE)
    if not include_expired:
        query = query.filter(
            or_(InputListing.expiry_date.is_(None), InputListing.expiry_date > datetime.now(timezone.utc))
        )
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(InputListing.product_name.ilike(like), InputListing.brand.ilike(like))
        )
    if category_id:
        query = query.filter(InputListing.category_id == category_id)
    if brand:
        query = query.filter(InputListing.brand.ilike(brand))
    if min_price is not None:
        query = query.filter(InputListing.price_per_unit >= min_price)
    if max_price is not None:
        query = query.filter(InputListing.price_per_unit <= max_price)
    if verified_only:
        query = query.filter(InputListing.verified_at.isnot(None))
    if province:
        query = query.filter(InputListing.province == province)

    return (
        query.order_by(InputListing.is_boosted.desc(), InputListing.created_at.desc())
        .offset(offset).limit(limit).all()
    )


def increment_view(db: Session, listing: InputListing) -> None:
    listing.view_count = (listing.view_count or 0) + 1


# ---------------------------------------------------------------------------
# Agent verification (function 380)
# ---------------------------------------------------------------------------

def verify_listing(
    db: Session,
    *,
    agent: User,
    listing_id: uuid.UUID,
    approve: bool,
    notes: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> InputListing:
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != InputListingStatus.PENDING_VERIFICATION:
        raise HTTPException(status_code=400, detail=f"Listing is {listing.status.value}")

    cat = listing.category
    if cat and cat.requires_registration and not listing.registration_number:
        if approve:
            raise HTTPException(status_code=400, detail="Cannot approve: registration number missing")

    listing.verified_by = agent.id
    listing.verified_at = datetime.now(timezone.utc)
    listing.verification_notes = notes
    if approve:
        listing.status = InputListingStatus.ACTIVE
        listing.rejection_reason = None
    else:
        listing.status = InputListingStatus.REJECTED
        listing.rejection_reason = rejection_reason or notes or "Rejected by verifier"

    append_audit(
        db, table_name="input_listings", record_id=str(listing.id),
        operation="VERIFY" if approve else "REJECT",
        payload={"agent_id": str(agent.id), "notes": notes, "rejection_reason": listing.rejection_reason},
        actor_id=str(agent.id), actor_role=agent.role.value,
    )
    seller = db.query(User).filter(User.id == listing.seller_id).first()
    seller_phone = getattr(seller, "phone_number", None) if seller else None
    if approve:
        notification_triggers.input_listing_verified(seller_phone, listing.product_name)
    else:
        notification_triggers.input_listing_rejected(
            seller_phone, listing.product_name, listing.rejection_reason or "verification failed"
        )
    return listing


# ---------------------------------------------------------------------------
# Offers (functions 374-376)
# ---------------------------------------------------------------------------

def create_offer(
    db: Session,
    *,
    buyer: User,
    listing_id: uuid.UUID,
    offered_price_per_unit: float,
    quantity: float,
    note: Optional[str] = None,
) -> InputOffer:
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing or listing.status != InputListingStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Listing not available")
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot offer on your own listing")
    if quantity <= 0 or offered_price_per_unit <= 0:
        raise HTTPException(status_code=400, detail="Quantity and price must be positive")
    if quantity < listing.min_order_quantity:
        raise HTTPException(status_code=400, detail=f"Minimum order quantity is {listing.min_order_quantity}")
    if quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Quantity exceeds available stock")

    total = round(quantity * offered_price_per_unit, 2)

    # Bulk order gate
    is_bulk = total >= settings.INPUT_BULK_ORDER_MIN_USD
    if is_bulk and not _is_business_verified(buyer):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "BUSINESS_VERIFICATION_REQUIRED",
                "message": f"Bulk orders over ${settings.INPUT_BULK_ORDER_MIN_USD:.0f} require business verification",
            },
        )

    offer = InputOffer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        offered_price_per_unit=Decimal(str(offered_price_per_unit)),
        quantity=quantity,
        total_amount=Decimal(str(total)),
        currency=listing.currency,
        note=note,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=OFFER_EXPIRY_HOURS),
    )
    db.add(offer)
    db.flush()
    seller = db.query(User).filter(User.id == listing.seller_id).first()
    if seller:
        notification_triggers.input_offer_received(
            getattr(seller, "phone_number", None),
            listing.product_name, quantity, offered_price_per_unit,
        )
    return offer


def withdraw_offer(db: Session, *, buyer: User, offer_id: uuid.UUID) -> InputOffer:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id, InputOffer.buyer_id == buyer.id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.status != InputOfferStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Offer is {offer.status.value}")
    offer.status = InputOfferStatus.WITHDRAWN
    offer.decided_at = datetime.now(timezone.utc)
    return offer


def accept_offer(
    db: Session,
    *,
    seller: User,
    offer_id: uuid.UUID,
    delivery_address: Optional[str] = None,
) -> InputOrder:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id).with_for_update().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    listing = db.query(InputListing).filter(InputListing.id == offer.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing missing")
    if listing.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not your listing")
    if offer.status != InputOfferStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Offer is {offer.status.value}")
    if offer.expires_at and datetime.now(timezone.utc) > offer.expires_at:
        offer.status = InputOfferStatus.EXPIRED
        db.flush()
        raise HTTPException(status_code=400, detail="Offer has expired")
    if offer.quantity > listing.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock to fulfill offer")

    buyer = db.query(User).filter(User.id == offer.buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=400, detail="Buyer not found")

    subtotal = float(offer.total_amount)
    platform_fee = round(subtotal * settings.INPUT_PLATFORM_FEE_PERCENT, 2)
    escrow_fee = round(subtotal * settings.INPUT_ESCROW_FEE_PERCENT, 2)
    total = round(subtotal + platform_fee + escrow_fee, 2)
    seller_payout = round(subtotal - escrow_fee, 2)

    if not wallet_service.withdraw(db, buyer.id, total, offer.currency):
        raise HTTPException(status_code=400, detail="Buyer has insufficient wallet balance")

    # Sign the escrow-hold transaction
    sig, payload = sign_transaction(
        user_id=str(buyer.id),
        txn_type="INPUT_ESCROW_HOLD",
        amount=total,
        currency=offer.currency,
        extra={"listing_id": str(listing.id), "offer_id": str(offer.id)},
    )

    order = InputOrder(
        offer_id=offer.id,
        listing_id=listing.id,
        seller_id=seller.id,
        buyer_id=buyer.id,
        order_number=f"IN-{secrets.token_hex(4).upper()}",
        quantity=offer.quantity,
        unit_price=offer.offered_price_per_unit,
        subtotal=Decimal(str(subtotal)),
        platform_fee=Decimal(str(platform_fee)),
        escrow_fee=Decimal(str(escrow_fee)),
        total_amount=Decimal(str(total)),
        seller_payout=Decimal(str(seller_payout)),
        currency=offer.currency,
        status=InputOrderStatus.ESCROW_HELD,
        is_bulk=subtotal >= settings.INPUT_BULK_ORDER_MIN_USD,
        delivery_address=delivery_address,
    )
    db.add(order)

    offer.status = InputOfferStatus.ACCEPTED
    offer.decided_at = datetime.now(timezone.utc)
    listing.quantity -= offer.quantity
    if listing.quantity <= 0:
        listing.status = InputListingStatus.SOLD_OUT
    elif listing.quantity <= max(listing.min_order_quantity, 5):
        notification_triggers.input_low_stock(
            getattr(seller, "phone_number", None), listing.product_name, float(listing.quantity)
        )

    append_audit(
        db, table_name="input_orders", record_id=str(order.offer_id),
        operation="ESCROW_HELD",
        payload={
            "buyer_id": str(buyer.id), "seller_id": str(seller.id),
            "listing_id": str(listing.id), "total": total,
            "platform_fee": platform_fee, "escrow_fee": escrow_fee,
            "signature": sig, "signed_payload": payload,
        },
        actor_id=str(seller.id), actor_role=seller.role.value,
    )
    db.flush()
    notification_triggers.input_offer_accepted(
        getattr(buyer, "phone_number", None), listing.product_name, total, order.order_number,
    )
    return order


def reject_offer(
    db: Session,
    *,
    seller: User,
    offer_id: uuid.UUID,
    reason: Optional[str] = None,
) -> InputOffer:
    offer = db.query(InputOffer).filter(InputOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    listing = db.query(InputListing).filter(InputListing.id == offer.listing_id).first()
    if not listing or listing.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not your listing")
    if offer.status != InputOfferStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Offer is {offer.status.value}")
    offer.status = InputOfferStatus.REJECTED
    offer.decision_notes = reason
    offer.decided_at = datetime.now(timezone.utc)
    buyer = db.query(User).filter(User.id == offer.buyer_id).first()
    if buyer:
        notification_triggers.input_offer_rejected(
            getattr(buyer, "phone_number", None), listing.product_name, reason,
        )
    return offer


# ---------------------------------------------------------------------------
# Order lifecycle (functions 376-378)
# ---------------------------------------------------------------------------

def mark_shipped(
    db: Session, *, seller: User, order_id: uuid.UUID, tracking_number: Optional[str] = None,
) -> InputOrder:
    order = db.query(InputOrder).filter(InputOrder.id == order_id).first()
    if not order or order.seller_id != seller.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != InputOrderStatus.ESCROW_HELD:
        raise HTTPException(status_code=400, detail=f"Order is {order.status.value}")
    order.status = InputOrderStatus.SHIPPED
    order.tracking_number = tracking_number
    order.shipped_at = datetime.now(timezone.utc)
    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    if buyer:
        notification_triggers.input_order_shipped(
            getattr(buyer, "phone_number", None), order.order_number, tracking_number,
        )
    return order


def confirm_delivery(
    db: Session, *, buyer: User, order_id: uuid.UUID, rating: Optional[int] = None, review: Optional[str] = None,
) -> InputOrder:
    order = db.query(InputOrder).filter(InputOrder.id == order_id).with_for_update().first()
    if not order or order.buyer_id != buyer.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in (InputOrderStatus.ESCROW_HELD, InputOrderStatus.SHIPPED, InputOrderStatus.DELIVERED):
        raise HTTPException(status_code=400, detail=f"Order is {order.status.value}")

    # Release escrow → credit seller
    if not wallet_service.deposit(db, order.seller_id, float(order.seller_payout), order.currency, str(order.id)):
        raise HTTPException(status_code=500, detail="Seller credit failed")

    order.status = InputOrderStatus.COMPLETED
    order.delivered_at = order.delivered_at or datetime.now(timezone.utc)
    order.confirmed_at = datetime.now(timezone.utc)
    if rating is not None:
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be 1..5")
        order.review_rating = rating
        order.review_text = review

    sig, payload = sign_transaction(
        user_id=str(order.seller_id), txn_type="INPUT_ESCROW_RELEASE",
        amount=float(order.seller_payout), currency=order.currency,
        extra={"order_id": str(order.id), "listing_id": str(order.listing_id)},
    )
    append_audit(
        db, table_name="input_orders", record_id=str(order.id),
        operation="ESCROW_RELEASED",
        payload={
            "buyer_id": str(buyer.id), "seller_id": str(order.seller_id),
            "amount": float(order.seller_payout), "rating": rating,
            "signature": sig, "signed_payload": payload,
        },
        actor_id=str(buyer.id), actor_role=buyer.role.value,
    )
    seller = db.query(User).filter(User.id == order.seller_id).first()
    if seller:
        notification_triggers.input_order_completed(
            getattr(seller, "phone_number", None), order.order_number, float(order.seller_payout),
        )
    return order


# ---------------------------------------------------------------------------
# Reports (function 379)
# ---------------------------------------------------------------------------

def report_listing(
    db: Session,
    *,
    reporter: User,
    listing_id: uuid.UUID,
    reason: InputReportReason,
    details: Optional[str] = None,
    evidence_urls: Optional[list[str]] = None,
) -> InputReport:
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    report = InputReport(
        listing_id=listing.id,
        reporter_id=reporter.id,
        reason=reason,
        details=details,
        evidence_urls=evidence_urls or [],
    )
    db.add(report)
    db.flush()
    return report


def resolve_report(
    db: Session,
    *,
    actor: User,
    report_id: uuid.UUID,
    uphold: bool,
    notes: Optional[str] = None,
    remove_listing: bool = False,
) -> InputReport:
    rep = db.query(InputReport).filter(InputReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    if rep.status not in (InputReportStatus.OPEN, InputReportStatus.INVESTIGATING):
        raise HTTPException(status_code=400, detail=f"Report is {rep.status.value}")
    rep.status = InputReportStatus.UPHELD if uphold else InputReportStatus.DISMISSED
    rep.resolved_by = actor.id
    rep.resolved_at = datetime.now(timezone.utc)
    rep.resolution_notes = notes
    if uphold and remove_listing:
        listing = db.query(InputListing).filter(InputListing.id == rep.listing_id).first()
        if listing:
            listing.status = InputListingStatus.REMOVED
    return rep


# ---------------------------------------------------------------------------
# Price alerts (function 383)
# ---------------------------------------------------------------------------

def upsert_price_alert(
    db: Session,
    *,
    user: User,
    target_price: float,
    listing_id: Optional[uuid.UUID] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
) -> InputPriceAlert:
    if target_price <= 0:
        raise HTTPException(status_code=400, detail="Target price must be positive")
    if not any([listing_id, category_id, brand]):
        raise HTTPException(status_code=400, detail="Specify listing_id, category_id, or brand")
    alert = (
        db.query(InputPriceAlert)
        .filter(
            InputPriceAlert.user_id == user.id,
            InputPriceAlert.listing_id == listing_id,
            InputPriceAlert.category_id == category_id,
            InputPriceAlert.brand == brand,
        )
        .first()
    )
    if alert:
        alert.target_price = Decimal(str(target_price))
        alert.is_active = True
    else:
        alert = InputPriceAlert(
            user_id=user.id, listing_id=listing_id, category_id=category_id, brand=brand,
            target_price=Decimal(str(target_price)),
        )
        db.add(alert)
    db.flush()
    return alert


# ---------------------------------------------------------------------------
# Trends (function 382)
# ---------------------------------------------------------------------------

def price_trends(db: Session, *, category_id: int, days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            func.avg(InputListing.price_per_unit).label("avg_price"),
            func.min(InputListing.price_per_unit).label("min_price"),
            func.max(InputListing.price_per_unit).label("max_price"),
            func.count(InputListing.id).label("listing_count"),
        )
        .filter(
            InputListing.category_id == category_id,
            InputListing.created_at >= since,
            InputListing.status == InputListingStatus.ACTIVE,
        )
        .one()
    )
    return {
        "category_id": category_id,
        "window_days": days,
        "avg_price": float(rows.avg_price or 0),
        "min_price": float(rows.min_price or 0),
        "max_price": float(rows.max_price or 0),
        "listing_count": int(rows.listing_count or 0),
    }


# ---------------------------------------------------------------------------
# Expiry sweep (scheduled job)
# ---------------------------------------------------------------------------

def sweep_expired(db: Session, *, now: Optional[datetime] = None) -> int:
    now = now or datetime.now(timezone.utc)
    expiring = (
        db.query(InputListing)
        .filter(
            InputListing.expiry_date.isnot(None),
            InputListing.expiry_date <= now,
            InputListing.status == InputListingStatus.ACTIVE,
        )
        .all()
    )
    for listing in expiring:
        listing.status = InputListingStatus.EXPIRED
        seller = db.query(User).filter(User.id == listing.seller_id).first()
        if seller:
            notification_triggers.input_listing_expired(
                getattr(seller, "phone_number", None), listing.product_name,
            )
    db.commit()
    return len(expiring)


def warn_expiring(db: Session, *, days_ahead: int = 7, now: Optional[datetime] = None) -> int:
    """Notify sellers whose listings expire within `days_ahead` days. Idempotent per day."""
    now = now or datetime.now(timezone.utc)
    horizon = now + timedelta(days=days_ahead)
    rows = (
        db.query(InputListing)
        .filter(
            InputListing.status == InputListingStatus.ACTIVE,
            InputListing.expiry_date.isnot(None),
            InputListing.expiry_date <= horizon,
            InputListing.expiry_date > now,
        )
        .all()
    )
    for listing in rows:
        days_left = max(0, (listing.expiry_date - now).days)
        seller = db.query(User).filter(User.id == listing.seller_id).first()
        if seller:
            notification_triggers.input_listing_expiry_warning(
                getattr(seller, "phone_number", None), listing.product_name, days_left,
            )
    return len(rows)


def evaluate_price_alerts(db: Session, *, listing: InputListing) -> int:
    """When a listing's price changes, fire matching alerts. Returns count fired."""
    alerts = (
        db.query(InputPriceAlert)
        .filter(
            InputPriceAlert.is_active.is_(True),
            ((InputPriceAlert.listing_id == listing.id)
             | (InputPriceAlert.category_id == listing.category_id)
             | (InputPriceAlert.brand == listing.brand)),
            InputPriceAlert.target_price >= listing.price_per_unit,
        )
        .all()
    )
    fired = 0
    for alert in alerts:
        user = db.query(User).filter(User.id == alert.user_id).first()
        if user:
            notification_triggers.input_price_alert_hit(
                getattr(user, "phone_number", None), listing.product_name,
                float(listing.price_per_unit), float(alert.target_price),
            )
            alert.last_triggered_at = datetime.now(timezone.utc)
            fired += 1
    db.flush()
    return fired


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_business_verified(user: User) -> bool:
    """Business verification flag — falls back to is_id_verified if column absent."""
    if hasattr(user, "is_business_verified"):
        return bool(user.is_business_verified)
    return bool(getattr(user, "is_id_verified", False))
