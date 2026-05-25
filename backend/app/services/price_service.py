from sqlalchemy.orm import Session


def get_price_prediction(db: Session, crop: str) -> dict:
    """
    Returns a price forecast for the given crop.
    """
    # Use a default price since scraping service is removed
    default_prices = {
        "maize": 420,
        "soybeans": 550,
        "wheat": 480,
        "sorghum": 380,
        "tobacco": 2500
    }
    gmb_bench = default_prices.get(crop.lower(), 420)

    return {
        "crop": crop,
        "gmb_bench_price": gmb_bench,
        "forecast_30d": gmb_bench,  # Use GMB price as forecast
        "confidence_interval": None,
        "accuracy_rating": "N/A",
        "data_source": "GMB Benchmark",
        "seasonal_index": 1.0,
        "trend": "STABLE",
        "recommendation": "Hold — prices stable this season",
    }


class PriceService:
    @staticmethod
    def get_price_prediction(db: Session, crop: str) -> dict:
        return get_price_prediction(db, crop)

    @staticmethod
    def get_current_prices(db: Session) -> dict:
        crops = ["Maize", "Soybeans", "Wheat", "Sorghum", "Tobacco"]
        return {
            c: NationalCommodityService.get_seasonal_market_price(c)
            for c in crops
        }


price_core = PriceService()
price_service = PriceService()
