from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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

@router.get("/forecast")
def get_market_forecast(
    crop: str = "Maize", 
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Returns standard market price data. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "Upgrade to PREMIUM for price forecasting."}
        
    return {"crop": crop, "current_price": 340.0, "suggested_price": 345.0, "status": "STABLE"}

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
        market_data[item["commodity"]] = {"price": item["price"], "unit": item["unit"], "origin": item["origin"]}
        
    return market_data


@router.get("/analytics/regional")
def get_regional_insights(
    user = Depends(get_current_user)
):
    """
    Regional market updates. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "Regional analytics require a PREMIUM subscription."}

    return [
        {"name": "Harare", "trend": "+12%", "crop": "Leafy Greens", "price": 0.85, "demand": "HIGH"},
        {"name": "Mash West", "trend": "+5%", "crop": "Maize", "price": 0.32, "demand": "CRITICAL"},
        {"name": "Midlands", "trend": "-2%", "crop": "Soya", "price": 0.58, "demand": "STABLE"},
        {"name": "Bulawayo", "trend": "+15%", "crop": "Poultry", "price": 4.50, "demand": "HIGH"},
        {"name": "Manicaland", "trend": "+8%", "crop": "Fruit", "price": 1.20, "demand": "MEDIUM"},
    ]

@router.get("/analytics/trends/{crop}")
def get_price_trends(
    crop: str,
    user = Depends(get_current_user)
):
    """
    Historical price trends. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "Historical trends are reserved for PREMIUM members."}

    history = [10, 10.5, 11, 10.8, 11.2, 11.8]
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    return [{"label": l, "value": v} for l, v in zip(labels, history)]

@router.get("/demand/{crop}")
def get_crop_demand(
    crop: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return {"crop": crop, "demand_index": 85.0, "status": "HIGH"}

@router.get("/risk/{user_id}")
def get_user_risk(
    user_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return {"user_id": user_id, "risk_score": 0.05, "status": "LOW_RISK"}

@router.get("/fraud-alerts")
def get_fraud_alerts(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return []

@router.get("/pulse")
def get_national_pulse(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Exposes the National Agri-Pulse Economic Indicator. Restricted to PREMIUM.
    """
    if user.role not in [UserRole.ADMIN, UserRole.AGENT] and user.subscription_tier == SubscriptionTier.BASIC:
        return {"error": "SUBSCRIPTION_REQUIRED", "message": "The National Pulse is a PREMIUM feature."}

    return {"index": 98.4, "status": "OPTIMAL"}
