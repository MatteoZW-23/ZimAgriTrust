import math
from datetime import date, datetime, timedelta
from statistics import mean, pstdev
from typing import Iterable, Optional

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.models.listing import Listing, ListingStatus, Offer
from app.models.price_history import PriceHistory
from app.models.transaction import Order, OrderStatus


BENCHMARK_PRICES = {
    "maize": 420,
    "soybeans": 550,
    "wheat": 480,
    "sorghum": 380,
    "tobacco": 2500,
    "honey": 3.5,
    "goats": 55,
    "goat": 55,
    "cattle": 450,
    "flowers": 1.25,
    "fish": 4.0,
    "eggs": 0.18,
    "milk": 0.75,
}


def _product_filter(product: str):
    pattern = f"%{product}%"
    return or_(
        Listing.product_type.ilike(pattern),
        Listing.product_subtype.ilike(pattern),
        cast(Listing.sector, String).ilike(pattern),
        Listing.crop.ilike(pattern),
        Listing.crop_type.ilike(pattern),
    )


def _avg(values: Iterable[float]) -> float:
    clean = [float(value) for value in values if value is not None and float(value) > 0]
    return mean(clean) if clean else 0.0


def _trend(recent: float, previous: float) -> str:
    if recent <= 0 or previous <= 0:
        return "STABLE"
    change_pct = ((recent - previous) / previous) * 100
    if change_pct >= 5:
        return "UP"
    if change_pct <= -5:
        return "DOWN"
    return "STABLE"


def _recommendation(trend: str, confidence: str) -> str:
    if confidence == "low":
        return "Use as an advisory signal only; more completed trades are needed before relying on this forecast."
    if trend == "UP":
        return "Prices are rising from observed platform history. Sellers can list confidently; buyers should secure supply early."
    if trend == "DOWN":
        return "Prices are softening from observed platform history. Buyers have negotiating room; sellers should prioritize quality and fast movement."
    return "Prices are broadly stable. Compete on grade, trust score, delivery speed, and verified quantity."


def get_price_prediction(
    db: Session,
    crop: str,
    province: Optional[str] = None,
    days_ahead: int = 30,
) -> dict:
    """
    Forecast price from platform history first, then active market signals, then
    static benchmarks as a final fallback.
    """
    product = crop.strip()
    days = max(1, min(days_ahead, 90))
    now = datetime.utcnow()
    recent_start = now - timedelta(days=90)
    previous_start = now - timedelta(days=180)
    today = date.today()
    history_start = today - timedelta(days=180)
    history_recent_start = today - timedelta(days=90)

    order_query = (
        db.query(Order)
        .join(Listing, Order.listing_id == Listing.id)
        .filter(
            Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]),
            Order.created_at >= previous_start,
            Order.quantity > 0,
        )
        .filter(_product_filter(product))
    )
    listing_query = (
        db.query(Listing)
        .filter(Listing.status == ListingStatus.ACTIVE)
        .filter(_product_filter(product))
    )
    offer_query = db.query(Offer).join(Listing).filter(_product_filter(product))
    history_query = db.query(PriceHistory).filter(
        PriceHistory.product_type.ilike(f"%{product}%"),
        PriceHistory.date >= history_start,
    )

    if province:
        order_query = order_query.filter(Listing.location_province.ilike(f"%{province}%"))
        listing_query = listing_query.filter(Listing.location_province.ilike(f"%{province}%"))
        offer_query = offer_query.filter(Listing.location_province.ilike(f"%{province}%"))
        history_query = history_query.filter(PriceHistory.location.ilike(f"%{province}%"))

    orders = order_query.all()
    recent_order_prices = [
        float(order.total_amount) / float(order.quantity)
        for order in orders
        if order.created_at and order.created_at >= recent_start and order.quantity and order.total_amount
    ]
    previous_order_prices = [
        float(order.total_amount) / float(order.quantity)
        for order in orders
        if order.created_at and previous_start <= order.created_at < recent_start and order.quantity and order.total_amount
    ]

    history_rows = history_query.all()
    recent_history_prices = [
        float(row.price_per_unit)
        for row in history_rows
        if row.date and row.date >= history_recent_start and row.price_per_unit
    ]
    previous_history_prices = [
        float(row.price_per_unit)
        for row in history_rows
        if row.date and history_start <= row.date < history_recent_start and row.price_per_unit
    ]

    active_listing_avg = float(listing_query.with_entities(func.avg(Listing.price_per_unit)).scalar() or 0)
    offer_avg = float(offer_query.with_entities(func.avg(Offer.offered_price_per_kg)).scalar() or 0)
    active_listing_count = listing_query.count()
    offer_count = offer_query.count()

    recent_market_prices = recent_order_prices + recent_history_prices
    previous_market_prices = previous_order_prices + previous_history_prices
    recent_avg = _avg(recent_market_prices)
    previous_avg = _avg(previous_market_prices)

    benchmark = BENCHMARK_PRICES.get(product.lower(), 0)
    components: list[tuple[float, float, str]] = []
    if recent_avg:
        components.append((recent_avg, 0.6, "completed_order_or_price_history"))
    if active_listing_avg:
        components.append((active_listing_avg, 0.3, "active_listing_prices"))
    if offer_avg:
        components.append((offer_avg, 0.1, "buyer_offer_prices"))
    if not components and benchmark:
        components.append((float(benchmark), 1.0, "benchmark_fallback"))

    weight_total = sum(weight for _, weight, _ in components) or 1.0
    predicted_price = sum(value * weight for value, weight, _ in components) / weight_total
    trend = _trend(recent_avg or active_listing_avg or predicted_price, previous_avg or predicted_price)
    sample_size = len(recent_market_prices) + active_listing_count + offer_count

    if len(recent_market_prices) >= 20:
        confidence = "high"
    elif len(recent_market_prices) >= 5 or active_listing_count >= 5 or offer_count >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    deviation_source = recent_market_prices or [active_listing_avg, offer_avg, float(benchmark or 0)]
    clean_deviation_source = [value for value in deviation_source if value > 0]
    if len(clean_deviation_source) > 1:
        deviation = pstdev(clean_deviation_source)
    else:
        deviation = predicted_price * 0.12
    margin = 1.28 * deviation / math.sqrt(max(1, len(clean_deviation_source)))

    return {
        "crop": product,
        "product": product,
        "province": province or "all",
        "forecast_days": days,
        "gmb_bench_price": benchmark or None,
        "forecast_30d": round(predicted_price, 2),
        "predicted_price": round(predicted_price, 2),
        "confidence_interval": {
            "low": round(max(0.0, predicted_price - margin), 2),
            "high": round(predicted_price + margin, 2),
        },
        "accuracy_rating": confidence,
        "data_source": ", ".join(dict.fromkeys(source for _, _, source in components)) or "insufficient_data",
        "model_type": "market_history_weighted_forecast",
        "training_status": "data_backed_not_ml_trained",
        "seasonal_index": 1.0,
        "trend": trend,
        "sample_size": sample_size,
        "historical_order_count": len(recent_order_prices),
        "price_history_count": len(recent_history_prices),
        "active_listing_count": active_listing_count,
        "offer_count": offer_count,
        "recommendation": _recommendation(trend, confidence),
    }


class PriceService:
    @staticmethod
    def get_price_prediction(db: Session, crop: str) -> dict:
        return get_price_prediction(db, crop)

    @staticmethod
    def get_current_prices(db: Session) -> dict:
        crops = ["Maize", "Soybeans", "Wheat", "Sorghum", "Tobacco"]
        return {
            crop: get_price_prediction(db, crop)
            for crop in crops
        }


price_core = PriceService()
price_service = PriceService()
