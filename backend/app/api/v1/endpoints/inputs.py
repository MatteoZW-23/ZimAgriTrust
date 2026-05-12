"""
Input marketplace endpoints — mounted at `/api/v1/inputs`.

Implements the 25 input-marketplace functions (#360-384).
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.input_marketplace import (
    InputCategory,
    InputListing,
    InputOffer,
    InputOrder,
    InputPriceAlert,
    InputReport,
    InputReportReason,
)
from app.models.user import User, UserRole
from app.schemas.inputs import (
    InputCategoryOut,
    InputCategoryUpsert,
    InputListingCreate,
    InputListingOut,
    InputListingUpdate,
    InputOfferCreate,
    InputOfferDecisionIn,
    InputOfferOut,
    InputOrderConfirmIn,
    InputOrderOut,
    InputOrderShipIn,
    InputPriceAlertIn,
    InputPriceAlertOut,
    InputReportIn,
    InputReportOut,
    InputReportResolveIn,
    InputVerificationDecisionIn,
)
from app.services import input_marketplace_service as svc

router = APIRouter()


_ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER)
_AGENT_ROLES = (UserRole.AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN)


# ---------------------------------------------------------------------------
# Categories (369, 381)
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=list[InputCategoryOut])
def list_categories(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    return svc.list_categories(db, active_only=active_only)


@router.post("/categories", response_model=InputCategoryOut)
def upsert_category(
    body: InputCategoryUpsert,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    cat = svc.upsert_category(
        db,
        slug=body.slug,
        name=body.name,
        description=body.description,
        requires_registration=body.requires_registration,
        requires_expiry=body.requires_expiry,
        requires_agent_verification=body.requires_agent_verification,
        is_regulated=body.is_regulated,
        is_active=body.is_active,
    )
    db.commit()
    db.refresh(cat)
    return cat


# ---------------------------------------------------------------------------
# Listings — CRUD + boost (360-368)
# ---------------------------------------------------------------------------

@router.post("/listings", response_model=InputListingOut, status_code=201)
def create_listing(
    body: InputListingCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    listing = svc.create_listing(
        db,
        seller=seller,
        category_id=body.category_id,
        product_name=body.product_name,
        quantity=body.quantity,
        price_per_unit=body.price_per_unit,
        unit=body.unit,
        brand=body.brand,
        description=body.description,
        photos=body.photos,
        documents=body.documents,
        expiry_date=body.expiry_date,
        registration_number=body.registration_number,
        location=body.location,
        province=body.province,
        min_order_quantity=body.min_order_quantity,
        currency=body.currency,
    )
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/listings", response_model=list[InputListingOut])
def search_listings(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    verified_only: bool = False,
    province: Optional[str] = None,
    seller_id: Optional[uuid.UUID] = None,
    include_expired: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return svc.search_listings(
        db, q=q, category_id=category_id, brand=brand,
        min_price=min_price, max_price=max_price,
        verified_only=verified_only, province=province,
        seller_id=seller_id, include_expired=include_expired,
        limit=limit, offset=offset,
    )


@router.get("/listings/me", response_model=list[InputListingOut])
def my_listings(
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    return svc.search_listings(db, seller_id=seller.id, include_expired=True, limit=200)


@router.get("/listings/{listing_id}", response_model=InputListingOut)
def get_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    listing = db.query(InputListing).filter(InputListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    svc.increment_view(db, listing)
    db.commit()
    return listing


@router.put("/listings/{listing_id}", response_model=InputListingOut)
def update_listing(
    listing_id: uuid.UUID,
    body: InputListingUpdate,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    listing = svc.update_listing(db, seller=seller, listing_id=listing_id, **body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    svc.delete_listing(db, seller=seller, listing_id=listing_id)
    db.commit()


@router.post("/listings/{listing_id}/boost", response_model=InputListingOut)
def boost_listing(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    listing = svc.boost_listing(db, seller=seller, listing_id=listing_id)
    db.commit()
    db.refresh(listing)
    return listing


# ---------------------------------------------------------------------------
# Verification (380)
# ---------------------------------------------------------------------------

@router.post("/listings/{listing_id}/verify", response_model=InputListingOut)
def verify_listing(
    listing_id: uuid.UUID,
    body: InputVerificationDecisionIn,
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(*_AGENT_ROLES)),
):
    listing = svc.verify_listing(
        db, agent=agent, listing_id=listing_id,
        approve=body.approve, notes=body.notes, rejection_reason=body.rejection_reason,
    )
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/listings/pending/queue", response_model=list[InputListingOut])
def pending_verification_queue(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(*_AGENT_ROLES)),
):
    return (
        db.query(InputListing)
        .filter(InputListing.status == "pending_verification")
        .order_by(InputListing.created_at.asc())
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# Offers (374-375)
# ---------------------------------------------------------------------------

@router.post("/listings/{listing_id}/offers", response_model=InputOfferOut, status_code=201)
def make_offer(
    listing_id: uuid.UUID,
    body: InputOfferCreate,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    offer = svc.create_offer(
        db, buyer=buyer, listing_id=listing_id,
        offered_price_per_unit=body.offered_price_per_unit,
        quantity=body.quantity, note=body.note,
    )
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/offers/me", response_model=list[InputOfferOut])
def my_offers(
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    return (
        db.query(InputOffer).filter(InputOffer.buyer_id == buyer.id)
        .order_by(InputOffer.created_at.desc()).all()
    )


@router.get("/offers/received", response_model=list[InputOfferOut])
def received_offers(
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    return (
        db.query(InputOffer)
        .join(InputListing, InputListing.id == InputOffer.listing_id)
        .filter(InputListing.seller_id == seller.id)
        .order_by(InputOffer.created_at.desc())
        .all()
    )


@router.post("/offers/{offer_id}/withdraw", response_model=InputOfferOut)
def withdraw_offer(
    offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    offer = svc.withdraw_offer(db, buyer=buyer, offer_id=offer_id)
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/accept", response_model=InputOrderOut)
def accept_offer(
    offer_id: uuid.UUID,
    body: InputOfferDecisionIn,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    order = svc.accept_offer(
        db, seller=seller, offer_id=offer_id, delivery_address=body.delivery_address,
    )
    db.commit()
    db.refresh(order)
    return order


@router.post("/offers/{offer_id}/reject", response_model=InputOfferOut)
def reject_offer(
    offer_id: uuid.UUID,
    body: InputOfferDecisionIn,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    offer = svc.reject_offer(db, seller=seller, offer_id=offer_id, reason=body.reason)
    db.commit()
    db.refresh(offer)
    return offer


# ---------------------------------------------------------------------------
# Orders (376-378)
# ---------------------------------------------------------------------------

@router.get("/orders/buying", response_model=list[InputOrderOut])
def my_buying(
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    return (
        db.query(InputOrder).filter(InputOrder.buyer_id == buyer.id)
        .order_by(InputOrder.created_at.desc()).all()
    )


@router.get("/orders/selling", response_model=list[InputOrderOut])
def my_selling(
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    return (
        db.query(InputOrder).filter(InputOrder.seller_id == seller.id)
        .order_by(InputOrder.created_at.desc()).all()
    )


@router.post("/orders/{order_id}/ship", response_model=InputOrderOut)
def ship_order(
    order_id: uuid.UUID,
    body: InputOrderShipIn,
    db: Session = Depends(get_db),
    seller: User = Depends(get_current_user),
):
    order = svc.mark_shipped(db, seller=seller, order_id=order_id, tracking_number=body.tracking_number)
    db.commit()
    db.refresh(order)
    return order


@router.post("/orders/{order_id}/confirm", response_model=InputOrderOut)
def confirm_order(
    order_id: uuid.UUID,
    body: InputOrderConfirmIn,
    db: Session = Depends(get_db),
    buyer: User = Depends(get_current_user),
):
    order = svc.confirm_delivery(db, buyer=buyer, order_id=order_id, rating=body.rating, review=body.review)
    db.commit()
    db.refresh(order)
    return order


# ---------------------------------------------------------------------------
# Reports (379)
# ---------------------------------------------------------------------------

@router.post("/listings/{listing_id}/report", response_model=InputReportOut, status_code=201)
def report_listing(
    listing_id: uuid.UUID,
    body: InputReportIn,
    db: Session = Depends(get_db),
    reporter: User = Depends(get_current_user),
):
    rep = svc.report_listing(
        db, reporter=reporter, listing_id=listing_id,
        reason=InputReportReason(body.reason), details=body.details,
        evidence_urls=body.evidence_urls,
    )
    db.commit()
    db.refresh(rep)
    return rep


@router.get("/reports/open", response_model=list[InputReportOut])
def list_open_reports(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_AGENT_ROLES)),
):
    return (
        db.query(InputReport).filter(InputReport.status.in_(["open", "investigating"]))
        .order_by(InputReport.created_at.asc()).all()
    )


@router.post("/reports/{report_id}/resolve", response_model=InputReportOut)
def resolve_report(
    report_id: uuid.UUID,
    body: InputReportResolveIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_AGENT_ROLES)),
):
    rep = svc.resolve_report(
        db, actor=actor, report_id=report_id,
        uphold=body.uphold, notes=body.notes, remove_listing=body.remove_listing,
    )
    db.commit()
    db.refresh(rep)
    return rep


# ---------------------------------------------------------------------------
# Trends + price alerts (382-383)
# ---------------------------------------------------------------------------

@router.get("/trends")
def trends(
    category_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return svc.price_trends(db, category_id=category_id, days=days)


@router.post("/price-alerts", response_model=InputPriceAlertOut, status_code=201)
def create_price_alert(
    body: InputPriceAlertIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = svc.upsert_price_alert(
        db, user=user, target_price=body.target_price,
        listing_id=body.listing_id, category_id=body.category_id, brand=body.brand,
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/price-alerts", response_model=list[InputPriceAlertOut])
def list_price_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(InputPriceAlert).filter(InputPriceAlert.user_id == user.id)
        .order_by(InputPriceAlert.created_at.desc()).all()
    )


@router.delete("/price-alerts/{alert_id}", status_code=204)
def delete_price_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = db.query(InputPriceAlert).filter(
        InputPriceAlert.id == alert_id, InputPriceAlert.user_id == user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
