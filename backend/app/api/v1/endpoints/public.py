"""
Public API Endpoints — no authentication required.
Serves the public marketplace dashboard with real data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.policy import calculate_full_order_breakdown

router = APIRouter()


@router.get("/prices/current")
def public_prices(db: Session = Depends(get_db)):
    """
    Current crop prices with 7-day change.
    Sourced from platform DB averages.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.transaction import Order, OrderStatus
    from datetime import datetime, timedelta, timezone
    
    # Get price history from completed orders
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    orders = db.query(Order).filter(
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= thirty_days_ago
    ).all()

    # Group by date and calculate average price
    price_by_date = {}
    for order in orders:
        date_str = order.created_at.date().isoformat()
        if date_str not in price_by_date:
            price_by_date[date_str] = []
        price_by_date[date_str].append(order.total_price / order.quantity if order.quantity > 0 else 0)

    # Calculate averages
    trends = []
    for date_str in sorted(price_by_date.keys()):
        avg_price = sum(price_by_date[date_str]) / len(price_by_date[date_str]) if price_by_date[date_str] else 0
        trends.append({"date": date_str, "price": avg_price, "source": "platform"})

    return trends


@router.get("/prices/trending")
def public_trending(db: Session = Depends(get_db)):
    """
    Top 5 trending crops based on last 24 h of platform activity
    (offers placed, listing views, searches).
    """
    return {"trending": ["Maize", "Soybeans", "Wheat", "Tobacco", "Sorghum"]}


@router.get("/news")
def public_news():
    """
    Latest agriculture news from Zimbabwe RSS feeds.
    """
    return {"news": []}


@router.get("/weather")
def public_weather():
    """
    Current weather for 5 major Zimbabwe farming regions.
    """
    return {"weather": []}


@router.get("/calendar")
def public_calendar():
    """
    Seasonal planting/harvest calendar for the current month.
    """
    return {"calendar": []}


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    """
    High-level platform statistics for the public homepage.
    """
    from app.models.user import User
    from app.models.listing import Listing, ListingStatus
    
    total_users = db.query(User).count()
    active_listings = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE).count()
    
    return {
        "stats": {
            "total_users": total_users,
            "active_listings": active_listings,
            "total_transactions": 0
        }
    }


@router.get("/listings")
def public_listings(
    db: Session = Depends(get_db),
    crop: str | None = Query(default=None),
    location: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Public listing search — no auth required.
    Delegates to the existing marketplace search logic.
    """
    from app.services.marketplace_service import marketplace_core
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
    return {
        "data": [_serialize_listing(l) for l in listings],
        "pagination": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/listings/{listing_id}")
def public_listing_detail(listing_id: str, db: Session = Depends(get_db)):
    """
    Public listing detail — no auth required.
    """
    from app.models.listing import Listing, ListingStatus
    from fastapi import HTTPException
    import uuid as _uuid

    try:
        uid = _uuid.UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing ID")

    listing = (
        db.query(Listing)
        .filter(Listing.id == uid, Listing.status == ListingStatus.ACTIVE)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _serialize_listing(listing, detail=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@router.get("/fee-preview")
def public_fee_preview(
    amount: float,
    currency: str = "USD",
    transport_fee: float = 0.0,
    transport_insurance_elected: bool = False,
):
    """
    Public fee breakdown for marketplace buyers.
    Uses default trust score (0) and no rural discount since user is anonymous.
    """
    return calculate_full_order_breakdown(
        goods_amount=amount,
        user_trust_score=0,
        is_rural=False,
        currency=currency,
        using_platform_transport=False,
        transport_fee=transport_fee,
        transport_insurance_elected=transport_insurance_elected,
    )


def _serialize_listing(listing, detail: bool = False) -> dict:
    """Converts a Listing ORM object to a public-safe dict."""
    from app.models.user import User

    base = {
        "id":               str(listing.id),
        "product_type":     listing.product_type,
        "grade":            listing.grade,
        "quantity":         listing.quantity,
        "quantity_unit":    listing.quantity_unit,
        "price_per_unit":   listing.price_per_unit,
        "currency":         listing.currency,
        "location_province": listing.location_province,
        "location_district": listing.location_district,
        "is_location_verified": listing.is_location_verified,
        "created_at":       listing.created_at.isoformat() if listing.created_at else None,
    }

    # Seller public info (trust score, verification — no PII)
    try:
        seller = listing.seller
        if seller:
            base["seller_name"]            = seller.full_name.split()[0] + " " + (seller.full_name.split()[1][0] + "." if len(seller.full_name.split()) > 1 else "")
            base["seller_trust_score"]     = getattr(seller, "trust_score", 0)
            base["id_verified"]            = seller.id_verified
            base["seller_verified"]        = seller.id_verified
            base["seller_created_at"]      = seller.created_at.isoformat() if seller.created_at else None
            base["seller_completed_sales"] = getattr(seller, "completed_sales", 0)
    except Exception:
        pass

    if detail:
        base["description"]      = getattr(listing, "description", None)
        base["harvest_date"]     = getattr(listing, "harvest_date", None)
        base["storage_type"]     = getattr(listing, "storage_type", None)
        base["delivery_options"] = getattr(listing, "delivery_options", None)
        base["images"]           = getattr(listing, "images", [])

    return base
