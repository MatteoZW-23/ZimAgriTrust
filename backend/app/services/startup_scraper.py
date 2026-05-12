"""
Startup Scraper — runs on every server boot and on a recurring schedule.

On startup:
  - Fires all price sources concurrently (ThreadPoolExecutor)
  - Fires all news RSS + HTML sources concurrently
  - Fires OpenWeatherMap for all 5 cities concurrently
  - Warms the in-memory caches so the first API request is instant

Background schedule (APScheduler):
  - Prices  : every 60 minutes
  - News    : every 60 minutes
  - Weather : every 6 hours

All jobs run in daemon threads — they never block the main event loop.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scheduler (APScheduler — already available via uvicorn's thread pool)
# We use BackgroundScheduler so it runs in a daemon thread, not the event loop.
# ---------------------------------------------------------------------------
_scheduler = None


def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            _scheduler = BackgroundScheduler(
                daemon=True,
                job_defaults={
                    "misfire_grace_time": 600,  # 10 min default grace
                    "coalesce": True,           # merge missed runs into one
                    "max_instances": 1,
                },
            )
        except ImportError:
            logger.warning(
                "APScheduler not installed — periodic scraping disabled. "
                "Run: pip install apscheduler"
            )
    return _scheduler


# ---------------------------------------------------------------------------
# Individual scrape jobs (called both at startup and by scheduler)
# ---------------------------------------------------------------------------

def _job_scrape_prices() -> None:
    """Scrape all price sources and warm the cache."""
    try:
        from app.services.scraper_service import AgriScraper, PRICE_SOURCES, _PRICE_TTL
        import app.services.scraper_service as _sc

        logger.info("SCRAPER | Starting price scrape across %d sources...", len(PRICE_SOURCES))
        all_prices: list[dict] = []

        with ThreadPoolExecutor(max_workers=len(PRICE_SOURCES), thread_name_prefix="price-scrape") as pool:
            futures = {pool.submit(AgriScraper._extract_prices_from_page, url): url for url in PRICE_SOURCES}
            for future in as_completed(futures, timeout=30):
                url = futures[future]
                try:
                    results = future.result()
                    if results:
                        logger.info("SCRAPER | %s → %d price(s) found", url, len(results))
                        all_prices.extend(results)
                    else:
                        logger.debug("SCRAPER | %s → no prices extracted", url)
                except Exception as exc:
                    logger.warning("SCRAPER | %s → failed: %s", url, exc)

        # Write directly into the scraper's cache
        _sc._price_cache = all_prices
        _sc._price_cache_time = datetime.utcnow()
        logger.info("SCRAPER | Price cache warmed — %d total price entries", len(all_prices))

    except Exception as e:
        logger.error("SCRAPER | Price job failed: %s", e)


def _job_scrape_news() -> None:
    """Scrape all news sources (RSS + HTML) and warm the cache."""
    try:
        from app.services.scraper_service import (
            AgriScraper, NEWS_RSS_SOURCES, NEWS_HTML_SOURCES,
        )
        import app.services.scraper_service as _sc

        all_sources = [
            ("rss",  src, url) for src, url in NEWS_RSS_SOURCES
        ] + [
            ("html", src, url) for src, url in NEWS_HTML_SOURCES
        ]

        logger.info("SCRAPER | Starting news scrape across %d sources...", len(all_sources))
        all_articles: list[dict] = []

        def _fetch(kind: str, source: str, url: str) -> list[dict]:
            if kind == "rss":
                return AgriScraper._parse_rss(url, source)
            return AgriScraper._scrape_html_headlines(url, source)

        with ThreadPoolExecutor(max_workers=len(all_sources), thread_name_prefix="news-scrape") as pool:
            futures = {
                pool.submit(_fetch, kind, source, url): (source, url)
                for kind, source, url in all_sources
            }
            for future in as_completed(futures, timeout=30):
                source, url = futures[future]
                try:
                    articles = future.result()
                    if articles:
                        logger.info("SCRAPER | %s → %d article(s)", source, len(articles))
                        all_articles.extend(articles)
                except Exception as exc:
                    logger.warning("SCRAPER | %s → failed: %s", source, exc)

        # Deduplicate by title
        seen: set[str] = set()
        unique: list[dict] = []
        for a in all_articles:
            key = a["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(a)

        _sc._news_cache = unique[:10]
        _sc._news_cache_time = datetime.utcnow()
        logger.info("SCRAPER | News cache warmed — %d unique articles", len(unique))

    except Exception as e:
        logger.error("SCRAPER | News job failed: %s", e)


def _job_warm_vision_model() -> None:
    """
    Ensures the vision model is loaded and ready.
    If custom weights are missing, downloads YOLOv8n base model once.
    """
    try:
        from app.ml.vision.crop_classifier import CropClassifier
        # Instantiating triggers the three-tier load logic
        clf = CropClassifier()
        if clf.model is not None:
            logger.info("VISION | Model ready: %s", type(clf.model).__name__)
        else:
            logger.info("VISION | Using OpenCV fallback classifier (no YOLO weights available)")
    except Exception as e:
        logger.warning("VISION | Model warm-up failed: %s", e)


def _job_scrape_weather() -> None:
    """Fetch weather for all 5 Zimbabwe cities and warm the cache."""
    try:
        import requests
        from app.services.public_data_service import (
            ZIMBABWE_CITIES, WEATHER_ICONS, FARMING_ADVICE,
        )
        import app.services.public_data_service as _pd

        api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        if not api_key:
            logger.info("SCRAPER | OPENWEATHER_API_KEY not set — skipping weather scrape")
            return

        logger.info("SCRAPER | Fetching weather for %d cities...", len(ZIMBABWE_CITIES))
        forecasts: list[dict] = []

        def _fetch_city(city: dict) -> dict | None:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={city['lat']}&lon={city['lon']}"
                f"&appid={api_key}&units=metric"
            )
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                return None
            data = resp.json()
            condition = data["weather"][0]["main"]
            return {
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
            }

        with ThreadPoolExecutor(max_workers=len(ZIMBABWE_CITIES), thread_name_prefix="weather-scrape") as pool:
            futures = {pool.submit(_fetch_city, city): city["name"] for city in ZIMBABWE_CITIES}
            for future in as_completed(futures, timeout=20):
                city_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        forecasts.append(result)
                        logger.info("SCRAPER | Weather OK: %s %s %d°C", city_name, result["icon"], result["temp_c"])
                except Exception as exc:
                    logger.warning("SCRAPER | Weather failed for %s: %s", city_name, exc)

        now = datetime.utcnow()
        _pd._weather_cache = {
            "forecasts":  forecasts,
            "updated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
            "available":  len(forecasts) > 0,
            "source":     "OpenWeatherMap",
        }
        _pd._weather_cache_time = now
        logger.info("SCRAPER | Weather cache warmed — %d/%d cities", len(forecasts), len(ZIMBABWE_CITIES))

    except Exception as e:
        logger.error("SCRAPER | Weather job failed: %s", e)


# ---------------------------------------------------------------------------
# Public API — called from main.py lifespan
# ---------------------------------------------------------------------------

def run_startup_scrape() -> None:
    """
    Fires all scrape jobs + vision model warm-up in background threads.
    Returns immediately — does not block the server startup.
    """
    logger.info("SCRAPER | ═══ STARTUP SCRAPE INITIATED (non-blocking) ═══")

    def _run_all():
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="startup-scrape") as pool:
            f_prices  = pool.submit(_job_scrape_prices)
            f_news    = pool.submit(_job_scrape_news)
            f_weather = pool.submit(_job_scrape_weather)
            f_vision  = pool.submit(_job_warm_vision_model)

            for future, name in [
                (f_prices,  "prices"),
                (f_news,    "news"),
                (f_weather, "weather"),
                (f_vision,  "vision model"),
            ]:
                try:
                    future.result(timeout=60)
                except Exception as exc:
                    logger.warning("SCRAPER | Startup %s did not complete: %s", name, exc)

        logger.info("SCRAPER | ═══ STARTUP SCRAPE COMPLETE ═══")

    import threading
    t = threading.Thread(target=_run_all, daemon=True, name="startup-scrape-main")
    t.start()


def start_scheduler() -> None:
    """
    Starts the background scheduler for periodic re-scraping.
    Safe to call multiple times — only starts once.
    """
    scheduler = _get_scheduler()
    if scheduler is None:
        return  # APScheduler not installed

    if scheduler.running:
        return

    # Prices: every 60 minutes
    scheduler.add_job(
        _job_scrape_prices,
        trigger="interval",
        minutes=60,
        id="scrape_prices",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,   # allow up to 10 min late before skipping
        coalesce=True,            # collapse multiple missed runs into one
        name="Price scraper (ZAMACE/GMB/AMA)",
    )

    # News: every 60 minutes
    scheduler.add_job(
        _job_scrape_news,
        trigger="interval",
        minutes=60,
        id="scrape_news",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
        coalesce=True,
        name="News scraper (RSS + HTML)",
    )

    # Weather: every 6 hours
    scheduler.add_job(
        _job_scrape_weather,
        trigger="interval",
        hours=6,
        id="scrape_weather",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=1800,
        coalesce=True,
        name="Weather (OpenWeatherMap)",
    )

    # Delivery auto-confirm: every 30 minutes
    def _job_auto_confirm_deliveries():
        _db = None
        try:
            from app.db.session import SessionLocal
            from app.services.delivery_service import auto_confirm_expired
            _db = SessionLocal()
            count = auto_confirm_expired(_db)
            if count:
                logger.info("SCHEDULER | Auto-confirmed %d deliveries", count)
        except Exception as e:
            logger.error("SCHEDULER | Auto-confirm job failed: %s", e)
        finally:
            if _db:
                _db.close()

    scheduler.add_job(
        _job_auto_confirm_deliveries,
        trigger="interval",
        minutes=30,
        id="auto_confirm_deliveries",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
        coalesce=True,
        name="Delivery auto-confirm (24h window)",
    )

    # ---------------- Recurring deposits (daily 06:00 UTC) ----------------
    def _job_recurring_deposits():
        _db = None
        try:
            from app.db.session import SessionLocal
            from app.services.deposit_automation_service import run_due_schedules
            _db = SessionLocal()
            count = run_due_schedules(_db)
            if count:
                logger.info("SCHEDULER | Recurring deposits processed: %d", count)
        except Exception as exc:  # noqa: BLE001
            logger.error("SCHEDULER | Recurring deposit job failed: %s", exc)
        finally:
            if _db:
                _db.close()

    scheduler.add_job(
        _job_recurring_deposits, trigger="cron", hour=6, minute=0,
        id="recurring_deposits", replace_existing=True, max_instances=1,
        coalesce=True, misfire_grace_time=3600,
        name="Recurring deposits (daily 06:00 UTC)",
    )

    # ---------------- Input listing expiry sweep + warnings (daily 08:00) ----
    def _job_input_expiry():
        _db = None
        try:
            from app.db.session import SessionLocal
            from app.services.input_marketplace_service import sweep_expired, warn_expiring
            _db = SessionLocal()
            expired = sweep_expired(_db)
            warned = warn_expiring(_db, days_ahead=7)
            if expired or warned:
                logger.info("SCHEDULER | Input listings expired=%d warned=%d", expired, warned)
        except Exception as exc:  # noqa: BLE001
            logger.error("SCHEDULER | Input expiry job failed: %s", exc)
        finally:
            if _db:
                _db.close()

    scheduler.add_job(
        _job_input_expiry, trigger="cron", hour=8, minute=0,
        id="input_expiry_sweep", replace_existing=True, max_instances=1,
        coalesce=True, misfire_grace_time=3600,
        name="Input listing expiry sweep + 7-day warning (daily 08:00 UTC)",
    )

    scheduler.start()
    logger.info(
        "SCRAPER | Scheduler started — prices/news every 60 min, weather every 6 h, "
        "delivery auto-confirm every 30 min, recurring deposits @06:00 UTC, "
        "input expiry sweep @08:00 UTC"
    )
