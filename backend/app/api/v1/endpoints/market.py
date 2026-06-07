from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.api.deps import get_db, get_current_user

router = APIRouter()

from app.models.user import UserRole

@router.get("/listings")
def get_market_listings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Compatibility endpoint for marketplace listing discovery.
    Mirrors active listings used by market-facing clients.
    """
    from app.models.listing import Listing, ListingStatus

    listings = (
        db.query(Listing)
        .filter(Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.created_at.desc())
        .limit(200)
        .all()
    )

    return [
        {
            "id": str(l.id),
            "title": l.title,
            "product_type": l.product_type,
            "quantity": float(l.quantity) if l.quantity is not None else 0.0,
            "quantity_unit": l.quantity_unit,
            "price_per_unit": float(l.price_per_unit) if l.price_per_unit is not None else 0.0,
            "location_province": l.location_province,
            "status": l.status.value if hasattr(l.status, "value") else str(l.status),
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in listings
    ]

@router.get("/news")
def get_market_news(user = Depends(get_current_user)):
    """
    Returns agricultural news.
    """
    return {"news": []}


@router.get("/summary")
def get_market_summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Unified market summary. Open to all registered users.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.transaction import Order, OrderStatus
    
    # Get active listings and recent orders
    active_listings = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE).all()
    recent_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).order_by(Order.created_at.desc()).limit(100).all()
    
    market_data = {}
    for listing in active_listings:
        if listing.product_type not in market_data:
            market_data[listing.product_type] = {"price": listing.price_per_unit, "unit": listing.quantity_unit, "origin": "platform"}
        
    return market_data


@router.get("/analytics/regional")
def get_regional_insights(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Regional market updates. Subscribers receive deeper UI treatment, not gated access."""

    from sqlalchemy import func
    from app.models.listing import Listing, ListingStatus

    stats = db.query(
        Listing.location_province,
        func.count(Listing.id).label("count"),
        func.avg(Listing.price_per_unit).label("avg_price")
    ).filter(Listing.status == ListingStatus.ACTIVE).group_by(Listing.location_province).all()
    
    return [
        {"province": s.location_province or "Other", "listings": s.count, "avg_price": round(s.avg_price, 2)}
        for s in stats
    ]


@router.get("/analytics/trends/{crop}")
def get_price_trends(
    crop: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Historical price trends from completed platform orders (last 30 days).
    """
    from app.models.listing import Listing
    from app.models.transaction import Order, OrderStatus
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import String, cast, or_

    # Get price history from completed orders
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    orders = db.query(Order).filter(
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= thirty_days_ago
    ).join(Listing, Order.listing_id == Listing.id).filter(
        or_(
            Listing.product_type.ilike(f"%{crop}%"),
            Listing.product_subtype.ilike(f"%{crop}%"),
            cast(Listing.sector, String).ilike(f"%{crop}%"),
            Listing.crop.ilike(f"%{crop}%"),
            Listing.crop_type.ilike(f"%{crop}%"),
        )
    ).all()

    # Group by date and calculate average price
    price_by_date = {}
    for order in orders:
        date_str = order.created_at.date().isoformat()
        if date_str not in price_by_date:
            price_by_date[date_str] = []
        price_by_date[date_str].append(order.total_amount / order.quantity if order.quantity > 0 else 0)

    # Calculate averages
    trends = []
    for date_str in sorted(price_by_date.keys()):
        avg_price = sum(price_by_date[date_str]) / len(price_by_date[date_str]) if price_by_date[date_str] else 0
        trends.append({"date": date_str, "price": avg_price, "source": "platform"})

    return trends


@router.get("/demand/{product}")
def get_crop_demand(
    product: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Calculates the Buy-to-Sell Ratio (Demand Index) for any agriculture product or sector.
    """
    from app.models.listing import Listing, Offer, ListingStatus
    from sqlalchemy import String, cast, func, or_

    product_match = or_(
        Listing.product_type.ilike(f"%{product}%"),
        Listing.product_subtype.ilike(f"%{product}%"),
        cast(Listing.sector, String).ilike(f"%{product}%"),
        Listing.crop.ilike(f"%{product}%"),
        Listing.crop_type.ilike(f"%{product}%"),
    )

    supply = db.query(func.sum(Listing.quantity)).filter(
        product_match,
        Listing.status == ListingStatus.ACTIVE
    ).scalar() or 0

    demand = db.query(func.sum(Offer.offered_quantity_kg)).join(Listing).filter(
        product_match
    ).scalar() or 0

    index = (demand / supply * 10) if supply > 0 else 0.0
    status = "HIGH" if index > 7 else "MODERATE" if index > 3 else "LOW"

    return {
        "crop": product,
        "product": product,
        "demand_index": round(index, 1),
        "status": status,
        "total_supply": supply,
        "total_demand": demand,
    }


@router.get("/risk/{target_user_id}")
def get_user_risk(
    target_user_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Security Engine: Evaluates a target user's risk profile.
    """
    from app.models.user import User
    from app.services.risk_service import evaluate_user_risk
    
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        return {"error": "USER_NOT_FOUND"}
        
    return evaluate_user_risk(db, target)


@router.get("/fraud-alerts")
def get_fraud_alerts(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Lists recent security and fraud alerts from the system audit log.
    """
    from app.models.system_audit import SystemAudit
    alerts = db.query(SystemAudit).filter(
        SystemAudit.action.in_(["SUSPICIOUS_TRANSACTION", "LEAKAGE_DETECTED", "RISK_LOCKDOWN"])
    ).order_by(SystemAudit.created_at.desc()).limit(10).all()
    
    return [
        {"id": str(a.id), "action": a.action, "note": a.note, "ts": a.created_at.isoformat()}
        for a in alerts
    ]

@router.get("/pulse")
def get_national_pulse(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Exposes the National Agri-Pulse Economic Indicator without blocking core users."""

    from app.services.revenue_service import AdminRevenueService
    stats = AdminRevenueService.get_national_revenue_summary(db)
    
    # Simple index calculation: Log10 of GMV + some vitality factor
    import math
    gmv = stats.get("gross_volume", 0)
    index = math.log10(gmv + 1) * 10
    
    status = "STABLE"
    if index > 50: status = "HIGH_LIQUIDITY"
    if index < 10: status = "EMERGING"

    return {
        "index": round(index, 1),
        "status": status,
        "gmv": gmv,
        "vitality": f"{min(100, index * 2):.1f}%"
    }


@router.get("/catalog")
def get_agri_catalog(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Returns the National Agricultural Database/Catalog.
    """
    return {"catalog": []}
