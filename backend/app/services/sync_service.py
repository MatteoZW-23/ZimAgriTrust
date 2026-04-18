import random
import uuid
import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, AgentProfile
from app.models.listing import Listing, ListingStatus, Sector, Offer, OfferStatus
from app.models.transaction import Transaction, TransactionType, Order, OrderStatus
from app.core.security import get_password_hash
from app.services.scraper_service import AgriScraper


# Structured Logging for Governance
logger = logging.getLogger(__name__)

def sync_system_data(db: Session):
    """
    Industrial-strength platform synchronization. 
    Uses atomic transactions to ensure data consistency.
    """
    logger.info("Initializing Platform Governance Sync...")
    
    # Standard security parameters
    admin_phone = "+263771000004"
    password = "password123"
    hashed_password = get_password_hash(password)
    pin_hash = get_password_hash("1234")

    try:
        # 1. UPSERT Administrator (MJ) - Essential System Access
        admin = db.query(User).filter(User.phone_number == admin_phone).first()
        if not admin:
            admin = User(
                full_name="MJ", phone_number=admin_phone, role=UserRole.ADMIN,
                password_hash=hashed_password, ussd_pin_hash=pin_hash,
                trust_score=100, province="Mashonaland Central", district="Harare", ward="Central",
                balance_usd=100000.0, national_id="REG-CORE-001"
            )
            db.add(admin)
            db.flush()

        logger.info("REAL-TIME MODE: Purging legacy demo data and initializing live sync...")
        
        # In real-time mode, we no longer pre-populate farmers or listings.
        # The system waits for real user registration and scrapes live market intelligence.
        
        db.commit()
        logger.info("Platform Live Sync Successful (Empty State initialized).")
        
        return {
            "status": "success",
            "message": "Platform initialized in Real-Time Mode.",
            "counts": {
                "system_admins": 1,
                "live_market_news": len(AgriScraper.scrape_latest_news()),
                "market_price_points": len(AgriScraper.scrape_market_prices())
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"PLATFORM SYNC ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "failure",
            "message": f"Sync Failed: {str(e)}"
        }
