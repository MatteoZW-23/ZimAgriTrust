from sqlalchemy.orm import Session
from app.ml.price_predictor import deep_engine
from app.services.national_commodity_service import NationalCommodityService


def get_price_prediction(db: Session, crop: str) -> dict:
    """
    Returns a price forecast for the given crop using live DB + scraper data.
    """
    forecast = deep_engine.forecast_price({}, db=db, crop=crop)

    # Also include GMB floor for reference
    gmb_bench = NationalCommodityService.get_seasonal_market_price(crop)

    return {
        "crop": crop,
        "gmb_bench_price": gmb_bench,
        "forecast_30d": forecast.get("forecasted_price"),
        "confidence_interval": forecast.get("confidence_interval"),
        "accuracy_rating": forecast.get("accuracy_rating"),
        "data_source": forecast.get("data_source"),
        "seasonal_index": forecast.get("seasonal_index"),
        "trend": "UPWARD" if (forecast.get("seasonal_index", 1.0) or 1.0) > 1.0 else "STABLE",
        "recommendation": (
            "Sell now — seasonal uplift active"
            if (forecast.get("seasonal_index", 1.0) or 1.0) > 1.02
            else "Hold — prices stable this season"
        ),
    }


class PriceService:
    @staticmethod
    def get_price_prediction(db: Session, crop: str) -> dict:
        return get_price_prediction(db, crop)

    @staticmethod
    def get_current_prices(db: Session) -> dict:
        crops = ["Maize", "Soybeans", "Wheat", "Sorghum", "Tobacco"]
        return {
            c: deep_engine.forecast_price({}, db=db, crop=c).get("forecasted_price")
            for c in crops
        }


price_core = PriceService()
price_service = PriceService()
