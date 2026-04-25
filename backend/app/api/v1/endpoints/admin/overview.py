from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.api.deps import get_db, require_roles
from app.models.listing import Listing, Offer
from app.models.user import User, UserRole
from app.models.transaction import Order, OrderStatus
from app.models.dispute import Dispute, DisputeStatus
from app.schemas.admin import AdminOverviewResponse

router = APIRouter()

@router.get("/overview", response_model=AdminOverviewResponse)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    total_vol = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    platform_rev = total_vol * 0.01

    # Real dispute counts
    open_disputes = db.query(Dispute).filter(
        Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW, DisputeStatus.ESCALATED])
    ).count()
    resolved_disputes = db.query(Dispute).filter(
        Dispute.status.in_([DisputeStatus.RESOLVED, DisputeStatus.CLOSED])
    ).count()

    # Average trust score
    avg_trust = db.query(func.avg(User.trust_score)).scalar() or 0.0

    # Escrow pool (sum of ESCROW_HELD orders)
    escrow_total = db.query(func.sum(Order.total_amount)).filter(
        Order.status == OrderStatus.ESCROW_HELD
    ).scalar() or 0.0

    # Average settlement time in hours (completed orders with updated_at - created_at)
    from sqlalchemy import cast, Float
    from datetime import datetime
    completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).limit(100).all()
    if completed_orders:
        deltas = [
            (o.updated_at - o.created_at).total_seconds() / 3600
            for o in completed_orders
            if o.updated_at and o.created_at
        ]
        avg_settlement_hours = round(sum(deltas) / len(deltas), 1) if deltas else None
    else:
        avg_settlement_hours = None

    return {
        "users": db.query(User).count(),
        "farmers": db.query(User).filter(User.role == UserRole.FARMER).count(),
        "buyers": db.query(User).filter(User.role == UserRole.BUYER).count(),
        "agents": db.query(User).filter(User.role == UserRole.AGENT).count(),
        "listings": db.query(Listing).count(),
        "total_volume": total_vol,
        "platform_revenue": platform_rev,
        "pending_verifications": db.query(Listing).filter(Listing.verification_status == "PENDING").count(),
        "suspended_listings": db.query(Listing).filter(Listing.status == "SUSPENDED").count(),
        "open_disputes": open_disputes,
        "resolved_disputes": resolved_disputes,
        "avg_trust_score": round(avg_trust, 1),
        "escrow_total": round(escrow_total, 2),
        "avg_settlement_hours": avg_settlement_hours,
        "stats": {
            "total_users": db.query(User).count(),
        },
        "system_health": {
            "api": "OPERATIONAL",
            "database": "OPERATIONAL",
            "ecocash": "CONNECTED",
            "ussd": "ACTIVE",
            "Market Analytics": "OPERATIONAL"
        }
    }

@router.get("/activities")
def get_all_activities(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    listings = db.query(Listing).options(joinedload(Listing.seller)).order_by(Listing.created_at.desc()).limit(20).all()
    offers = db.query(Offer).options(joinedload(Offer.buyer), joinedload(Offer.listing)).order_by(Offer.created_at.desc()).limit(20).all()
    orders = db.query(Order).options(joinedload(Order.buyer), joinedload(Order.seller), joinedload(Order.listing)).order_by(Order.created_at.desc()).limit(20).all()

    return {
        "listings": [
            {
                "id": str(l.id), "product": l.product_type, "qty": l.quantity, 
                "price": l.price_per_unit, "seller": l.seller.full_name, "status": str(l.status)
            } for l in listings
        ],
        "offers": [
            {
                "id": str(o.id), "product": o.listing.product_type, "qty": o.quantity,
                "offered_price": o.offered_price, "buyer": o.buyer.full_name, "status": str(o.status)
            } for o in offers
        ],
        "deals": [
            {
                "id": str(d.id), "deal_no": d.order_number, "product": d.listing.product_type,
                "amount": d.total_amount, "status": str(d.status), "buyer": d.buyer.full_name, "seller": d.seller.full_name
            } for d in orders
        ]
    }
