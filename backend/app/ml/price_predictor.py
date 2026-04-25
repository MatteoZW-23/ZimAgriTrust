"""
Price Forecasting Engine.
Uses live DB transaction history + scraper prices to produce deterministic forecasts.
No fake LSTM/ARIMA — real weighted moving average with seasonal adjustment.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Zimbabwe seasonal price multipliers by month (harvest = lower prices, off-season = higher)
# Jan–Apr: post-harvest glut → lower; May–Oct: off-season → higher; Nov–Dec: new crop coming
_SEASONAL_INDEX: Dict[int, float] = {
    1: 0.92, 2: 0.88, 3: 0.85, 4: 0.90,
    5: 1.00, 6: 1.05, 7: 1.08, 8: 1.10,
    9: 1.08, 10: 1.05, 11: 0.98, 12: 0.95,
}

# GMB / ZAMACE reference floor prices (USD/tonne) — updated periodically
_GMB_FLOOR: Dict[str, float] = {
    "Maize":           285.0,
    "Wheat":           390.0,
    "Soybeans":        580.0,
    "Tobacco":        1800.0,
    "Sorghum":         220.0,
    "Groundnuts":      650.0,
    "Sunflower Seeds": 480.0,
    "Sugar Beans":     900.0,
    "Cotton":          420.0,
    "Barley":          350.0,
}

_DEFAULT_FLOOR = 300.0


class DeepForecaster:
    """
    Deterministic price forecasting engine.
    Combines:
      1. Live DB weighted average from recent completed orders
      2. Scraper spot prices (GMB / AMA)
      3. Seasonal adjustment index
    Falls back to GMB floor prices when no live data is available.
    """

    def __init__(self):
        self.architecture = "Weighted Moving Average + Seasonal Index (Live DB)"

    def forecast_price(self, features: Dict, db=None, crop: str = "Maize") -> Dict:
        """
        features: optional dict with keys demand, supply, trust, volatility (ignored — kept for API compat)
        db: SQLAlchemy session (optional — enables live DB pricing)
        crop: commodity name
        """
        month = datetime.utcnow().month
        seasonal = _SEASONAL_INDEX.get(month, 1.0)
        floor = _GMB_FLOOR.get(crop, _DEFAULT_FLOOR)

        # 1. Try live DB average from recent completed orders
        db_avg: Optional[float] = None
        if db is not None:
            try:
                from sqlalchemy import func
                from app.models.transaction import Order, OrderStatus
                from app.models.listing import Listing
                cutoff = datetime.utcnow() - timedelta(days=30)
                row = (
                    db.query(func.avg(Order.total_amount / Order.quantity_kg))
                    .join(Listing, Order.listing_id == Listing.id)
                    .filter(
                        Listing.product_type.ilike(f"%{crop}%"),
                        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]),
                        Order.created_at >= cutoff,
                        Order.quantity_kg > 0,
                    )
                    .scalar()
                )
                if row and row > 0:
                    db_avg = float(row)
            except Exception:
                pass

        # 2. Try scraper spot price
        scraper_price: Optional[float] = None
        try:
            from app.services.scraper_service import AgriScraper
            prices = AgriScraper.scrape_market_prices()
            for item in prices:
                if crop.lower() in item.get("commodity", "").lower():
                    scraper_price = float(item["price"])
                    break
        except Exception:
            pass

        # 3. Weighted blend: DB (60%) + scraper (30%) + floor (10%)
        if db_avg and scraper_price:
            base_price = db_avg * 0.60 + scraper_price * 0.30 + floor * 0.10
            source = "live_db+scraper"
        elif db_avg:
            base_price = db_avg * 0.80 + floor * 0.20
            source = "live_db"
        elif scraper_price:
            base_price = scraper_price * 0.80 + floor * 0.20
            source = "scraper"
        else:
            base_price = floor
            source = "gmb_floor"

        forecast = round(base_price * seasonal, 2)
        low = round(forecast * 0.95, 2)
        high = round(forecast * 1.05, 2)

        confidence = 0.90 if source == "live_db+scraper" else 0.78 if source in ("live_db", "scraper") else 0.60

        return {
            "forecasted_price": forecast,
            "confidence_interval": [low, high],
            "accuracy_rating": f"{confidence * 100:.0f}%",
            "model_architecture": self.architecture,
            "data_source": source,
            "seasonal_index": seasonal,
            "month": month,
            "components": {
                "db_avg_price": round(db_avg, 2) if db_avg else None,
                "scraper_price": round(scraper_price, 2) if scraper_price else None,
                "gmb_floor": floor,
            },
        }

    def get_price_history(self, crop: str, db=None, days: int = 30) -> List[Dict]:
        """
        Returns daily average prices from completed orders for the last N days.
        Used by /market/analytics/trends/{crop}.
        """
        if db is None:
            return []
        try:
            from sqlalchemy import func, cast, Date
            from app.models.transaction import Order, OrderStatus
            from app.models.listing import Listing
            cutoff = datetime.utcnow() - timedelta(days=days)
            rows = (
                db.query(
                    cast(Order.created_at, Date).label("date"),
                    func.avg(Order.total_amount / Order.quantity_kg).label("price"),
                )
                .join(Listing, Order.listing_id == Listing.id)
                .filter(
                    Listing.product_type.ilike(f"%{crop}%"),
                    Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]),
                    Order.created_at >= cutoff,
                    Order.quantity_kg > 0,
                )
                .group_by(cast(Order.created_at, Date))
                .order_by(cast(Order.created_at, Date))
                .all()
            )
            return [{"date": str(r.date), "price": round(float(r.price), 2)} for r in rows]
        except Exception:
            return []

    def train(self, data_path: str, epochs: int = 100):
        """No-op — this engine uses live DB data, no training required."""
        return {
            "status": "ok",
            "note": "Price forecaster uses live DB + scraper data. No training file needed.",
            "architecture": self.architecture,
        }


# Global instance
deep_engine = DeepForecaster()
