from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.api.deps import get_db, get_current_user

router = APIRouter()

from app.models.user import SubscriptionTier, UserRole
from app.services.scraper_service import AgriScraper

@router.get("/news")
def get_market_news(user = Depends(get_current_user)):
    """
    Returns live-scraped agricultural news from the National Network.
    """
    return AgriScraper.scrape_latest_news()


@router.get("/summary")
def get_market_summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Unified market summary. Open to all registered users.
    NOW POWERED BY LIVE MARKET SCRAPING.
    """
    scraped_prices = AgriScraper.scrape_market_prices()
    market_data = {}
    for item in scraped_prices:
        market_data[item["commodity"]] = {"price": item["price"], "unit": item["unit"], "origin": item.get("source", "")}
        
    return market_data


@router.get("/analytics/regional")
def get_regional_insights(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Regional market updates. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "Regional analytics require a PREMIUM subscription."}

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
    Falls back to scraper spot prices when no order history exists.
    """
    from app.ml.price_predictor import deep_engine as price_engine

    # Try live DB history first
    history = price_engine.get_price_history(crop, db=db, days=30)
    if history:
        return history

    # Fallback: scraper spot price as a single data point
    try:
        from app.services.scraper_service import AgriScraper
        prices = AgriScraper.scrape_market_prices()
        for item in prices:
            if crop.lower() in item.get("commodity", "").lower():
                today = datetime.utcnow().date().isoformat()
                return [{"date": today, "price": item["price"], "source": item.get("source", "scraper")}]
    except Exception:
        pass

    return []


@router.get("/demand/{crop}")
def get_crop_demand(
    crop: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Calculates the Buy-to-Sell Ratio (Demand Index) for a specific crop.
    """
    from app.models.listing import Listing, Offer, ListingStatus
    from sqlalchemy import func
    
    supply = db.query(func.sum(Listing.quantity)).filter(
        Listing.product_type.ilike(f"%{crop}%"),
        Listing.status == ListingStatus.ACTIVE
    ).scalar() or 0
    
    demand = db.query(func.sum(Offer.quantity)).join(Listing).filter(
        Listing.product_type.ilike(f"%{crop}%")
    ).scalar() or 0
    
    index = (demand / supply * 10) if supply > 0 else 0.0
    status = "HIGH" if index > 7 else "MODERATE" if index > 3 else "LOW"
    
    return {"crop": crop, "demand_index": round(index, 1), "status": status, "total_supply": supply, "total_demand": demand}


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
    """
    Exposes the National Agri-Pulse Economic Indicator. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "The National Pulse is a PREMIUM feature."}

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
    from app.services.national_commodity_service import NationalCommodityService
    return NationalCommodityService.SECTOR_GRADING_REGISTRY

