"""
Public Data Service — real data only, no hardcoded prices or fake numbers.

Priority chain for each data type:
  Prices   : live web scrape → DB average of active listings → omit crop
  Trending : real offer + listing activity from DB → empty list
  News     : RSS feeds → HTML scrape → empty list
  Weather  : OpenWeatherMap API (requires OPENWEATHER_API_KEY) → empty list
  Calendar : date-aware agronomic data (factual, not market data)
  Stats    : live DB counts → zeros (never fake numbers)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services.scraper_service import AgriScraper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Crop catalogue — metadata only, NO base prices
# ---------------------------------------------------------------------------
CROP_CATALOGUE = [
    {"name": "Maize",       "emoji": "🌽", "unit": "kg"},
    {"name": "Soybeans",    "emoji": "🫘", "unit": "kg"},
    {"name": "Wheat",       "emoji": "🌾", "unit": "kg"},
    {"name": "Sugar Beans", "emoji": "🫘", "unit": "kg"},
    {"name": "Groundnuts",  "emoji": "🥜", "unit": "kg"},
    {"name": "Tobacco",     "emoji": "🍃", "unit": "kg"},
    {"name": "Sorghum",     "emoji": "🌾", "unit": "kg"},
    {"name": "Tomatoes",    "emoji": "🍅", "unit": "kg"},
]

_TONNE_TO_KG = 1000.0

# ---------------------------------------------------------------------------
# Price history cache — stores last known real price per crop for 7-day delta
# ---------------------------------------------------------------------------
_price_history: dict[str, list[tuple[datetime, float]]] = {}  # crop → [(ts, price)]


def _record_price(crop: str, price: float) -> None:
    history = _price_history.setdefault(crop, [])
    history.append((datetime.utcnow(), price))
    # Keep only last 8 days
    cutoff = datetime.utcnow() - timedelta(days=8)
    _price_history[crop] = [(ts, p) for ts, p in history if ts >= cutoff]


def _get_7d_change(crop: str, current: float) -> tuple[float, str]:
    """Returns (change_pct, direction) based on real recorded history."""
    history = _price_history.get(crop, [])
    cutoff = datetime.utcnow() - timedelta(days=7)
    old_prices = [p for ts, p in history if ts <= cutoff]
    if not old_prices:
        return 0.0, "flat"
    old_price = old_prices[-1]
    if old_price == 0:
        return 0.0, "flat"
    change = round(((current - old_price) / old_price) * 100, 1)
    direction = "up" if change > 0 else ("down" if change < 0 else "flat")
    return change, direction


# ---------------------------------------------------------------------------
# 1. CROP PRICE TRENDS
# ---------------------------------------------------------------------------

def get_price_trends(db: Session) -> dict:
    """
    Returns real current prices for major crops.
    Source priority: live web scrape → DB average of active listings.
    Crops with no real data are omitted from the response.
    """
    from app.models.listing import Listing, ListingStatus

    # Get live scraped prices
    scraped_raw = AgriScraper.scrape_market_prices()
    scraped_map: dict[str, float] = {}
    for item in scraped_raw:
        name = item["commodity"].lower()
        price = float(item["price"])
        unit  = item.get("unit", "t").lower()
        # Normalise to USD/kg
        if unit in ("t", "tonne", "ton"):
            price = price / _TONNE_TO_KG
        scraped_map[name] = round(price, 4)

    # Get DB averages for active listings
    db_map: dict[str, tuple[float, int]] = {}  # crop_key → (avg_price, count)
    try:
        rows = (
            db.query(
                Listing.product_type,
                func.avg(Listing.price_per_unit).label("avg_price"),
                func.count(Listing.id).label("cnt"),
            )
            .filter(Listing.status == ListingStatus.ACTIVE, Listing.currency == "USD")
            .group_by(Listing.product_type)
            .all()
        )
        for row in rows:
            if row.product_type and row.avg_price:
                db_map[row.product_type.lower()] = (round(float(row.avg_price), 4), row.cnt)
    except Exception as e:
        logger.warning("DB price query failed: %s", e)

    results = []
    for crop in CROP_CATALOGUE:
        name      = crop["name"]
        name_key  = name.lower()
        first_word = name.split()[0].lower()

        # Try scraped price
        price = scraped_map.get(name_key) or scraped_map.get(first_word)

        # Try DB average
        listing_count = 0
        if price is None:
            for key, (avg, cnt) in db_map.items():
                if first_word in key or key in name_key:
                    price = avg
                    listing_count = cnt
                    break
        else:
            # Get listing count from DB even when we have a scraped price
            for key, (_, cnt) in db_map.items():
                if first_word in key or key in name_key:
                    listing_count = cnt
                    break

        if price is None:
            continue  # No real data — skip this crop entirely

        _record_price(name, price)
        change_pct, direction = _get_7d_change(name, price)

        source = "ZAMACE/GMB (live)" if (name_key in scraped_map or first_word in scraped_map) else "Platform listings avg"

        results.append({
            "crop":       name,
            "emoji":      crop["emoji"],
            "price_usd":  price,
            "unit":       crop["unit"],
            "change_pct": change_pct,
            "direction":  direction,
            "listings":   listing_count,
            "source":     source,
        })

    return {
        "prices":     results,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "source":     "ZAMACE / GMB / Platform listings",
    }


# ---------------------------------------------------------------------------
# 2. TRENDING CROPS — real platform activity only
# ---------------------------------------------------------------------------

def get_trending_crops(db: Session) -> dict:
    """
    Ranks crops by real offer + listing activity in the last 24 hours.
    Returns empty list when there is no activity — never fake data.
    """
    from app.models.listing import Listing, ListingStatus, Offer

    cutoff = datetime.utcnow() - timedelta(hours=24)
    trends: dict[str, dict] = {}

    # Offer activity (strongest demand signal)
    try:
        offer_rows = (
            db.query(Listing.product_type, func.count(Offer.id).label("cnt"))
            .join(Offer, Offer.listing_id == Listing.id)
            .filter(Offer.created_at >= cutoff)
            .group_by(Listing.product_type)
            .order_by(func.count(Offer.id).desc())
            .limit(10)
            .all()
        )
        for row in offer_rows:
            crop = row.product_type or "Unknown"
            trends.setdefault(crop, {"offers": 0, "listings": 0})
            trends[crop]["offers"] += row.cnt
    except Exception as e:
        logger.warning("Offer trend query failed: %s", e)

    # Active listing count (supply signal)
    try:
        listing_rows = (
            db.query(Listing.product_type, func.count(Listing.id).label("cnt"))
            .filter(Listing.status == ListingStatus.ACTIVE)
            .group_by(Listing.product_type)
            .order_by(func.count(Listing.id).desc())
            .limit(10)
            .all()
        )
        for row in listing_rows:
            crop = row.product_type or "Unknown"
            trends.setdefault(crop, {"offers": 0, "listings": 0})
            trends[crop]["listings"] += row.cnt
    except Exception as e:
        logger.warning("Listing trend query failed: %s", e)

    scored = [
        {
            "crop":     crop,
            "emoji":    next((c["emoji"] for c in CROP_CATALOGUE if c["name"].lower() in crop.lower()), "🌱"),
            "score":    d["offers"] * 3 + d["listings"],
            "offers":   d["offers"],
            "listings": d["listings"],
            "label":    "🔥 HOT" if d["offers"] > 5 else ("📈 Rising" if d["offers"] > 1 else "🟡 Active"),
        }
        for crop, d in trends.items()
        if d["offers"] > 0 or d["listings"] > 0
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "trending":     scored[:5],
        "window_hours": 24,
        "updated_at":   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }


# ---------------------------------------------------------------------------
# 3. NEWS — RSS feeds + HTML scraping, no static fallback
# ---------------------------------------------------------------------------

def get_news() -> dict:
    """
    Returns real agriculture news from Zimbabwe RSS feeds / HTML scraping.
    Returns empty articles list when all sources are unreachable.
    """
    articles = AgriScraper.scrape_latest_news()
    return {
        "articles":   articles,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "live":       len(articles) > 0,
    }


# ---------------------------------------------------------------------------
# 4. WEATHER — OpenWeatherMap only
# ---------------------------------------------------------------------------

ZIMBABWE_CITIES = [
    {"name": "Harare",    "lat": -17.8252, "lon": 31.0335},
    {"name": "Bulawayo",  "lat": -20.1325, "lon": 28.6264},
    {"name": "Mutare",    "lat": -18.9707, "lon": 32.6709},
    {"name": "Gweru",     "lat": -19.4500, "lon": 29.8167},
    {"name": "Masvingo",  "lat": -20.0667, "lon": 30.8333},
]

WEATHER_ICONS = {
    "Clear": "☀️", "Clouds": "⛅", "Rain": "🌧️",
    "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Snow": "❄️",
    "Mist": "🌫️", "Fog": "🌫️",
}

FARMING_ADVICE = {
    "Clear": "Good for harvesting",
    "Clouds": "Normal conditions",
    "Rain": "Caution for storage",
    "Drizzle": "Light rain — monitor crops",
    "Thunderstorm": "Avoid field work",
    "Snow": "Protect crops",
    "Mist": "Watch for fungal risk",
    "Fog": "Watch for fungal risk",
}

_weather_cache: dict | None = None
_weather_cache_time: datetime | None = None
_WEATHER_TTL = 21600  # 6 hours


def get_weather() -> dict:
    """
    Returns live weather for 5 Zimbabwe farming regions via OpenWeatherMap.
    Requires OPENWEATHER_API_KEY environment variable.
    Returns empty forecasts list when API key is absent or API fails.
    """
    global _weather_cache, _weather_cache_time

    now = datetime.utcnow()
    if _weather_cache is not None and _weather_cache_time is not None:
        if (now - _weather_cache_time).total_seconds() < _WEATHER_TTL:
            return _weather_cache

    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    forecasts = []

    if api_key:
        for city in ZIMBABWE_CITIES:
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?lat={city['lat']}&lon={city['lon']}"
                    f"&appid={api_key}&units=metric"
                )
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    condition = data["weather"][0]["main"]
                    forecasts.append({
                        "city":      city["name"],
                        "temp_c":    round(data["main"]["temp"]),
                        "feels_c":   round(data["main"]["feels_like"]),
                        "condition": condition,
                        "desc":      data["weather"][0]["description"].capitalize(),
                        "icon":      WEATHER_ICONS.get(condition, "🌡️"),
                        "rain_mm":   round(data.get("rain", {}).get("1h", 0), 1),
                        "humidity":  data["main"]["humidity"],
                        "wind_kph":  round(data["wind"]["speed"] * 3.6, 1),
                        "advice":    FARMING_ADVICE.get(condition, "Normal conditions"),
                    })
                else:
                    logger.warning("OpenWeatherMap returned %s for %s", resp.status_code, city["name"])
            except Exception as e:
                logger.warning("Weather fetch failed for %s: %s", city["name"], e)
    else:
        logger.info("OPENWEATHER_API_KEY not set — weather data unavailable")

    result = {
        "forecasts":  forecasts,
        "updated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "available":  len(forecasts) > 0,
        "source":     "OpenWeatherMap" if forecasts else "Unavailable — set OPENWEATHER_API_KEY",
    }
    _weather_cache = result
    _weather_cache_time = now
    return result


# ---------------------------------------------------------------------------
# 5. SEASONAL CALENDAR — agronomic facts, not market data
# ---------------------------------------------------------------------------

# Zimbabwe agronomic calendar — factual planting/harvest windows
SEASONAL_DATA: dict[int, list[dict]] = {
    1:  [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Growing",     "note": "Peak growing season — monitor for pests and armyworm"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Growing",     "note": "Flowering stage — critical water period"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Harvest",     "note": "Summer harvest — high supply period"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Growing",     "note": "Topping and suckering phase"},
    ],
    2:  [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Maturing",    "note": "Grain filling — protect from birds"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Maturing",    "note": "Pod filling — reduce irrigation"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Harvest",     "note": "Peak supply period"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Ripening",    "note": "Leaf ripening — prepare for reaping"},
    ],
    3:  [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Harvest",     "note": "Early harvest begins — Grade A opportunity"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Harvest",     "note": "Harvest window opens — sell early for premium"},
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Land prep",   "note": "Prepare fields for winter wheat planting"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Reaping",     "note": "Auction season approaching"},
    ],
    4:  [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Harvest",     "note": "Main harvest season (March–June)"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Harvest",     "note": "Harvest window open"},
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Planting soon","note": "Winter wheat planting begins next month (May)"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Peak season", "note": "High supply — prices typically lower"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Auction",     "note": "Auction floors open"},
    ],
    5:  [
        {"crop": "Maize",       "emoji": "🌽", "activity": "Post-harvest", "note": "Dry and store — prices typically rise Aug–Oct"},
        {"crop": "Wheat",       "emoji": "🌾", "activity": "Planting",     "note": "Winter wheat planting in irrigated areas"},
        {"crop": "Groundnuts",  "emoji": "🥜", "activity": "Harvest",      "note": "Harvest and dry before storage"},
        {"crop": "Tobacco",     "emoji": "🍃", "activity": "Auction",      "note": "Peak auction season"},
    ],
    6:  [
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Growing",     "note": "Winter wheat growing — frost risk in highlands"},
        {"crop": "Maize",    "emoji": "🌽", "activity": "Storage",     "note": "Stored grain — prices stabilising"},
        {"crop": "Potatoes", "emoji": "🥔", "activity": "Planting",    "note": "Winter potato planting in irrigated areas"},
    ],
    7:  [
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Growing",     "note": "Tillering stage — apply top dressing"},
        {"crop": "Potatoes", "emoji": "🥔", "activity": "Growing",     "note": "Hilling and irrigation critical"},
        {"crop": "Maize",    "emoji": "🌽", "activity": "Storage",     "note": "Stored grain prices rising — good selling window"},
    ],
    8:  [
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Heading",     "note": "Heading stage — watch for rust disease"},
        {"crop": "Potatoes", "emoji": "🥔", "activity": "Harvest",     "note": "Winter potato harvest"},
        {"crop": "Maize",    "emoji": "🌽", "activity": "Storage",     "note": "Peak storage prices — sell before new season"},
    ],
    9:  [
        {"crop": "Wheat",    "emoji": "🌾", "activity": "Harvest",     "note": "Wheat harvest — sell to GMB or open market"},
        {"crop": "Maize",    "emoji": "🌽", "activity": "Land prep",   "note": "Prepare fields for summer planting"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Land prep",   "note": "Prepare for October planting"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Planting",    "note": "Spring tomato planting"},
    ],
    10: [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Planting",    "note": "Summer planting begins with first rains"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Planting",    "note": "Optimal planting window: Oct 15 – Nov 15"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Seedbed",     "note": "Seedbed preparation"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Growing",     "note": "Spring crop growing"},
    ],
    11: [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Growing",     "note": "Germination and early growth — weed control critical"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Growing",     "note": "Vegetative stage — nodulation check"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Transplanting","note": "Transplant seedlings to main field"},
        {"crop": "Cotton",   "emoji": "🌿", "activity": "Planting",    "note": "Cotton planting season"},
    ],
    12: [
        {"crop": "Maize",    "emoji": "🌽", "activity": "Growing",     "note": "Knee-high stage — top dress with nitrogen"},
        {"crop": "Soybeans", "emoji": "🫘", "activity": "Growing",     "note": "Branching stage — monitor for aphids"},
        {"crop": "Tobacco",  "emoji": "🍃", "activity": "Growing",     "note": "Rapid growth phase — irrigation critical"},
        {"crop": "Tomatoes", "emoji": "🍅", "activity": "Harvest",     "note": "Summer harvest begins"},
    ],
}

SEASONAL_TIPS: dict[int, str] = {
    1:  "Rainy season peak — ensure good drainage to prevent waterlogging.",
    2:  "Monitor crops closely as they approach maturity.",
    3:  "Early harvest brings premium prices — act fast.",
    4:  "Maize harvest season — secure dry storage before rains end.",
    5:  "Dry season begins — plan irrigation for winter crops.",
    6:  "Winter planting window — wheat and potatoes in irrigated areas.",
    7:  "Mid-winter — stored grain prices rising, good time to sell.",
    8:  "Wheat heading — watch for disease, harvest approaching.",
    9:  "Spring prep — land preparation for summer crops.",
    10: "First rains expected — plant maize and soybeans promptly.",
    11: "Growing season underway — weed and pest control critical.",
    12: "Summer crops growing — top-dress and monitor moisture.",
}


def get_seasonal_calendar() -> dict:
    month = datetime.utcnow().month
    return {
        "month":   datetime.utcnow().strftime("%B %Y"),
        "entries": SEASONAL_DATA.get(month, []),
        "tip":     SEASONAL_TIPS.get(month, ""),
    }


# ---------------------------------------------------------------------------
# 6. PLATFORM STATS — live DB counts only
# ---------------------------------------------------------------------------

def get_platform_stats(db: Session) -> dict:
    """
    Returns live platform statistics from the database.
    Returns zeros when DB is unavailable — never fake numbers.
    """
    from app.models.listing import Listing, ListingStatus
    from app.models.transaction import Order, OrderStatus
    from app.models.user import User

    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_listings = (
            db.query(func.count(Listing.id))
            .filter(Listing.status == ListingStatus.ACTIVE)
            .scalar() or 0
        )
        total_orders = (
            db.query(func.count(Order.id))
            .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]))
            .scalar() or 0
        )
        total_volume = (
            db.query(func.sum(Order.total_amount))
            .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED]))
            .scalar() or 0
        )
        return {
            "users":        int(total_users),
            "listings":     int(total_listings),
            "transactions": int(total_orders),
            "volume_usd":   round(float(total_volume), 2),
        }
    except Exception as e:
        logger.error("Stats DB query failed: %s", e)
        return {"users": 0, "listings": 0, "transactions": 0, "volume_usd": 0.0}
