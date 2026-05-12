"""
Admin Scraping & Data Pipeline Control Center.
Gives admins manual control over every scraper, cache, and cleaning pipeline.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────────

def _cache_age_seconds(cache_time) -> int | None:
    if cache_time is None:
        return None
    return int((datetime.utcnow() - cache_time).total_seconds())


# ── STATUS ─────────────────────────────────────────────────────────────────────

@router.get("/status")
def scraper_status(_: User = Depends(require_roles(UserRole.ADMIN))):
    """
    Returns live cache state for every scraper:
    age, item count, last-scraped timestamp, scheduler job status.
    """
    import app.services.scraper_service as sc

    # Scheduler job info
    scheduler_jobs: list[dict] = []
    try:
        from app.services.startup_scraper import _get_scheduler
        sched = _get_scheduler()
        if sched and sched.running:
            for job in sched.get_jobs():
                nxt = job.next_run_time
                scheduler_jobs.append({
                    "id":       job.id,
                    "name":     job.name,
                    "next_run": nxt.isoformat() if nxt else None,
                    "running":  True,
                })
        else:
            scheduler_jobs = [{"id": "scheduler", "name": "APScheduler", "running": False}]
    except Exception as e:
        scheduler_jobs = [{"id": "scheduler", "name": f"Error: {e}", "running": False}]

    news_age  = _cache_age_seconds(sc._news_cache_time)
    price_age = _cache_age_seconds(sc._price_cache_time)

    return {
        "scrapers": {
            "news": {
                "cached_items":  len(sc._news_cache)  if sc._news_cache  else 0,
                "cache_age_sec": news_age,
                "last_scraped":  sc._news_cache_time.isoformat()  if sc._news_cache_time  else None,
                "ttl_sec":       sc._NEWS_TTL,
                "stale":         news_age  is None or news_age  > sc._NEWS_TTL,
                "sources":       [s for s, _ in sc.NEWS_RSS_SOURCES],
            },
            "prices": {
                "cached_items":  len(sc._price_cache) if sc._price_cache else 0,
                "cache_age_sec": price_age,
                "last_scraped":  sc._price_cache_time.isoformat() if sc._price_cache_time else None,
                "ttl_sec":       sc._PRICE_TTL,
                "stale":         price_age is None or price_age > sc._PRICE_TTL,
                "sources":       sc.PRICE_SOURCES,
            },
            "weather": {
                "cached_items":  0,   # weather cache lives in public_data_service
                "last_scraped":  None,
                "sources":       ["OpenWeatherMap API"],
            },
        },
        "scheduler_jobs": scheduler_jobs,
    }


# ── MANUAL SCRAPE TRIGGERS ─────────────────────────────────────────────────────

@router.post("/run/prices")
def run_price_scrape(_: User = Depends(require_roles(UserRole.ADMIN))):
    """Force-refresh the commodity price cache from all sources."""
    try:
        import app.services.scraper_service as sc
        # Bust cache so scraper re-fetches
        sc._price_cache      = None
        sc._price_cache_time = None
        prices = sc.AgriScraper.scrape_market_prices()
        return {
            "status":  "success",
            "scraped": len(prices),
            "items":   prices,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/news")
def run_news_scrape(_: User = Depends(require_roles(UserRole.ADMIN))):
    """Force-refresh the agriculture news cache from all RSS/HTML sources."""
    try:
        import app.services.scraper_service as sc
        sc._news_cache      = None
        sc._news_cache_time = None
        news = sc.AgriScraper.scrape_latest_news()
        return {
            "status":  "success",
            "scraped": len(news),
            "items":   news,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/weather")
def run_weather_scrape(_: User = Depends(require_roles(UserRole.ADMIN))):
    """Force-refresh weather data for all Zimbabwe farming regions."""
    try:
        from app.services.public_data_service import get_weather
        # public_data_service.get_weather() has its own cache — pass a dummy db
        weather = get_weather()
        return {
            "status":  "success",
            "scraped": len(weather) if isinstance(weather, list) else 1,
            "items":   weather,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/all")
def run_all_scrapers(_: User = Depends(require_roles(UserRole.ADMIN))):
    """Run all scrapers concurrently and return a combined summary."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import app.services.scraper_service as sc

    # Bust all caches
    sc._price_cache = sc._price_cache_time = None
    sc._news_cache  = sc._news_cache_time  = None

    results: dict[str, Any] = {}

    def _scrape_prices():
        return "prices", sc.AgriScraper.scrape_market_prices()

    def _scrape_news():
        return "news", sc.AgriScraper.scrape_latest_news()

    def _scrape_weather():
        from app.services.public_data_service import get_weather
        return "weather", get_weather()

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="admin-scrape") as pool:
        futures = [pool.submit(f) for f in (_scrape_prices, _scrape_news, _scrape_weather)]
        try:
            for future in as_completed(futures, timeout=45):
                try:
                    key, data = future.result()
                    results[key] = {
                        "status":  "success",
                        "scraped": len(data) if isinstance(data, list) else 1,
                    }
                except Exception as e:
                    results[str(e)[:20]] = {"status": "error", "error": str(e)}
        except TimeoutError:
            # Handle timeout gracefully - return partial results
            for future in futures:
                if not future.done():
                    future.cancel()
            results["_timeout"] = {
                "status": "warning",
                "message": "Some scrapers timed out after 45s. Partial results returned."
            }

    return {"status": "complete", "results": results, "scraped_at": datetime.utcnow().isoformat()}


# ── DATA CLEANING PIPELINE ─────────────────────────────────────────────────────

@router.post("/clean/prices")
def clean_price_data(_: User = Depends(require_roles(UserRole.ADMIN))):
    """
    Run the data integrity pipeline on the current price cache:
    - IQR outlier removal
    - Unit normalisation (tonnes → kg)
    - Commodity name standardisation
    - Export timestamped CSV snapshot
    """
    try:
        import app.services.scraper_service as sc
        from app.services.data_integrity_service import data_integrity

        raw = sc._price_cache or sc.AgriScraper.scrape_market_prices()
        if not raw:
            return {"status": "no_data", "message": "No price data in cache. Run price scraper first."}

        cleaned = data_integrity.clean_scraped_prices(raw)
        data_integrity.export_production_snapshot("prices", cleaned)

        removed = len(raw) - len(cleaned)
        return {
            "status":          "success",
            "raw_count":       len(raw),
            "clean_count":     len(cleaned),
            "outliers_removed": removed,
            "items":           cleaned,
            "exported_to":     "data/processed/snapshots/",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean/listings")
def clean_listing_data(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Run the ML preprocessing pipeline on active listing data:
    - Duplicate removal
    - Median imputation for missing numeric fields
    - Physical constraint enforcement (price > 0, quantity > 0)
    - Feature engineering (hour, is_peak_hour, is_high_value)
    - Export CSV snapshot
    """
    try:
        import pandas as pd
        from app.ml.preprocessing import cleaner, engineer
        from app.models.listing import Listing, ListingStatus
        from app.services.data_integrity_service import data_integrity

        rows = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE).all()
        if not rows:
            return {"status": "no_data", "message": "No active listings found."}

        records = [
            {
                "id":            str(r.id),
                "product_type":  r.product_type,
                "price_per_unit": float(r.price_per_unit or 0),
                "quantity_kg":   float(r.quantity_kg or 0),
                "created_at":    r.created_at.isoformat() if r.created_at else None,
                "location":      r.location_province,
            }
            for r in rows
        ]

        df = pd.DataFrame(records)
        df_clean = cleaner.run_pipeline(df)
        df_feat  = engineer.engineer_all_features(df_clean)

        data_integrity.export_production_snapshot("listings", df_feat.to_dict("records"))

        return {
            "status":          "success",
            "raw_count":       len(records),
            "clean_count":     len(df_feat),
            "removed":         len(records) - len(df_feat),
            "features_added":  [c for c in df_feat.columns if c not in df.columns],
            "exported_to":     "data/processed/snapshots/",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean/transactions")
def clean_transaction_data(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Clean and feature-engineer completed transaction data for ML training.
    Outputs fraud-detector-ready feature vectors.
    """
    try:
        import numpy as np
        import pandas as pd
        from app.ml.preprocessing import cleaner, engineer
        from app.models.transaction import Order, OrderStatus
        from app.services.data_integrity_service import data_integrity

        orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).all()
        if not orders:
            return {"status": "no_data", "message": "No completed transactions found."}

        records = []
        for o in orders:
            amount = float(o.total_amount or 0)
            qty    = float(o.quantity_kg or 0)
            price  = (amount / qty) if qty > 0 else 0
            hour   = o.created_at.hour if o.created_at else 12
            records.append({
                "order_id":       str(o.id),
                "amount":         amount,
                "quantity":       qty,
                "price_per_kg":   price,
                "hour":           hour,
                "farmer_history": 1,
                "buyer_history":  1,
                "is_off_hour":    int(hour < 6 or hour > 22),
                "log_amount":     float(np.log1p(amount)),
                "log_quantity":   float(np.log1p(qty)),
                "created_at":     o.created_at.isoformat() if o.created_at else None,
                "total_amount":   amount,
            })

        df = pd.DataFrame(records)
        df_clean = cleaner.run_pipeline(df)
        df_feat  = engineer.engineer_all_features(df_clean)

        data_integrity.export_production_snapshot("transactions", df_feat.to_dict("records"))

        return {
            "status":      "success",
            "raw_count":   len(records),
            "clean_count": len(df_feat),
            "removed":     len(records) - len(df_feat),
            "exported_to": "data/processed/snapshots/",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean/all")
def run_full_pipeline(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Run all cleaning pipelines in sequence and return a combined report."""
    from fastapi.testclient import TestClient  # not used — call functions directly

    report: dict[str, Any] = {}

    for name, fn, needs_db in [
        ("prices",       clean_price_data,       False),
        ("listings",     clean_listing_data,      True),
        ("transactions", clean_transaction_data,  True),
    ]:
        try:
            kwargs = {"db": db} if needs_db else {}
            # Call the function directly (bypass FastAPI dependency injection)
            if needs_db:
                result = fn.__wrapped__(db=db, _=None) if hasattr(fn, "__wrapped__") else fn(db=db, _=None)
            else:
                result = fn.__wrapped__(_=None) if hasattr(fn, "__wrapped__") else fn(_=None)
            report[name] = result
        except Exception as e:
            report[name] = {"status": "error", "error": str(e)}

    return {"status": "complete", "pipelines": report, "ran_at": datetime.utcnow().isoformat()}


# ── CACHE MANAGEMENT ──────────────────────────────────────────────────────────

@router.delete("/cache")
def clear_all_caches(_: User = Depends(require_roles(UserRole.ADMIN))):
    """Bust all in-memory scraper caches, forcing fresh fetches on next request."""
    import app.services.scraper_service as sc
    sc._price_cache = sc._price_cache_time = None
    sc._news_cache  = sc._news_cache_time  = None
    return {"status": "cleared", "cleared_at": datetime.utcnow().isoformat()}


@router.get("/snapshots")
def list_snapshots(_: User = Depends(require_roles(UserRole.ADMIN))):
    """List all exported CSV snapshots in the processed data directory."""
    import os
    processed_dir = "data/processed/snapshots"
    if not os.path.exists(processed_dir):
        return {"snapshots": []}

    files = []
    for fname in sorted(os.listdir(processed_dir), reverse=True):
        if fname.endswith(".csv"):
            fpath = os.path.join(processed_dir, fname)
            stat  = os.stat(fpath)
            files.append({
                "filename":   fname,
                "size_kb":    round(stat.st_size / 1024, 1),
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return {"snapshots": files}
