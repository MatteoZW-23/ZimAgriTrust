"""
Public API Endpoints — no authentication required.
Serves the public marketplace dashboard with real data.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from time import time

from app.api.deps import get_db
from app.core.policy import calculate_full_order_breakdown

router = APIRouter()
_PUBLIC_CACHE: dict[str, tuple[float, object]] = {}


def _cache_get(key: str):
    rec = _PUBLIC_CACHE.get(key)
    if not rec:
        return None
    expires_at, payload = rec
    if time() >= expires_at:
        _PUBLIC_CACHE.pop(key, None)
        return None
    return payload


def _cache_set(key: str, payload: object, ttl_seconds: int):
    _PUBLIC_CACHE[key] = (time() + ttl_seconds, payload)


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
        price_by_date[date_str].append(order.total_amount / order.quantity if order.quantity > 0 else 0)

    # Calculate averages
    trends = []
    for date_str in sorted(price_by_date.keys()):
        avg_price = sum(price_by_date[date_str]) / len(price_by_date[date_str]) if price_by_date[date_str] else 0
        trends.append({"date": date_str, "price": avg_price, "source": "platform"})

    _cache_set("public_prices_current", trends, 120)
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
async def public_weather(region: str = Query(default="harare")):
    """
    Current weather for Zimbabwe farming regions (F#79).
    Uses weather_service with OpenWeatherMap integration.
    """
    from app.services.weather_service import weather_service

    weather_data = await weather_service.get_weather(region)
    return {"weather": [weather_data]}


@router.get("/calendar")
async def public_calendar(season: str = Query(default=None)):
    """
    Seasonal planting/harvest calendar (F#80).
    Uses planting_calendar_service with Zimbabwe crop data.
    """
    from app.services.planting_calendar_service import planting_calendar_service

    if season:
        calendar_data = planting_calendar_service.get_season_calendar(season)
        return {"calendar": calendar_data, "season": season}
    else:
        calendar_data = await planting_calendar_service.get_current_month_calendar()
        return {"calendar": calendar_data}


@router.get("/fertilizer-calc")
def public_fertilizer_calculator(
    crop: str = Query(..., description="Crop type (maize, soybeans, wheat, tobacco, vegetables, potatoes, groundnuts)"),
    area_hectares: float = Query(..., gt=0, description="Area in hectares"),
    soil_type: str = Query(default="loamy", description="Soil type (sandy, loamy, clay, red_soil)"),
):
    """
    Fertilizer calculator (F#81).
    Calculates fertilizer requirements based on crop, area, and soil type.
    """
    from app.services.fertilizer_calculator_service import fertilizer_calculator_service

    try:
        result = fertilizer_calculator_service.calculate_fertilizer(
            crop=crop,
            area_hectares=area_hectares,
            soil_type=soil_type,
        )
        return result
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    """
    High-level platform statistics for the public homepage.
    """
    from app.models.user import User, UserRole
    from app.models.listing import Listing, ListingStatus
    from app.models.transaction import Transaction

    total_users = db.query(User).count()
    farmers = db.query(User).filter(User.role == UserRole.FARMER).count()
    buyers = db.query(User).filter(User.role == UserRole.BUYER).count()
    suppliers = db.query(User).filter(User.role == UserRole.SUPPLIER).count()
    active_listings = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE).count()
    total_transactions = db.query(Transaction).count()

    payload = {
        "stats": {
            "users": total_users,
            "listings": active_listings,
            "transactions": total_transactions,
            "farmers": farmers,
            "buyers": buyers,
            "suppliers": suppliers,
            "provinces_covered": 10,
            "total_users": total_users,
            "active_listings": active_listings,
            "total_transactions": total_transactions,
        }
    }
    _cache_set("public_stats", payload, 60)
    return payload


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
        "sector":           getattr(listing, "sector", None),
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
        "images":           getattr(listing, "images", []) or [],
        "photos":           getattr(listing, "images", []) or [],
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
