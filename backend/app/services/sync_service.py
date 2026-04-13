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
        # 1. UPSERT Administrator (MJ)
        admin = db.query(User).filter(User.phone_number == admin_phone).first()
        if not admin:
            admin = User(
                full_name="MJ", phone_number=admin_phone, role=UserRole.ADMIN,
                password_hash=hashed_password, ussd_pin_hash=pin_hash,
                trust_score=100, province="Mashonaland Central", district="Harare", ward="Central",
                balance_usd=50000.0, national_id="29-1234567-X-00"
            )
            db.add(admin)
            db.flush()

        # 2. SEED Multiple Farmers
        farmers_data = [
            {"name": "T. Miller", "phone": "+263771000001", "prov": "Mashonaland Central", "dist": "Mazowe"},
            {"name": "D. Roberts", "phone": "+263772111222", "prov": "Matabeleland North", "dist": "Lupane"},
            {"name": "A. Peterson", "phone": "+263773333444", "prov": "Midlands", "dist": "Kwekwe"},
            {"name": "M. Watson", "phone": "+263774555666", "prov": "Manicaland", "dist": "Nyanga"},
            {"name": "R. Sterling", "phone": "+263775777888", "prov": "Masvingo", "dist": "Chiredzi"}
        ]
        
        farmers = []
        for f in farmers_data:
            user = db.query(User).filter(User.phone_number == f["phone"]).first()
            if not user:
                user = User(
                    full_name=f["name"], phone_number=f["phone"], role=UserRole.FARMER,
                    password_hash=hashed_password, ussd_pin_hash=pin_hash,
                    trust_score=random.randint(75, 98), province=f["prov"], district=f["dist"],
                    balance_usd=random.uniform(500, 2500)
                )
                db.add(user)
                db.flush()
            farmers.append(user)

        # 3. SEED Multiple Buyers
        buyers_data = [
            {"name": "Harare Grain Millers", "phone": "+263771000002", "prov": "Harare", "dist": "Harare"},
            {"name": "Bulawayo Beef Co", "phone": "+263776111333", "prov": "Bulawayo", "dist": "Bulawayo"},
            {"name": "Zimbabwe Leaf Tobacco", "phone": "+263777222444", "prov": "Mashonaland West", "dist": "Banket"}
        ]
        
        buyers = []
        for b in buyers_data:
            user = db.query(User).filter(User.phone_number == b["phone"]).first()
            if not user:
                user = User(
                    full_name=b["name"], phone_number=b["phone"], role=UserRole.BUYER,
                    password_hash=hashed_password, ussd_pin_hash=pin_hash,
                    trust_score=random.randint(85, 99), province=b["prov"], district=b["dist"],
                    balance_usd=random.uniform(10000, 50000)
                )
                db.add(user)
                db.flush()
            buyers.append(user)

        # 4. Regional Agents
        agent_user = db.query(User).filter(User.phone_number == "+263771000003").first()
        if not agent_user:
            agent_user = User(
                full_name="S. Richards", phone_number="+263771000003", role=UserRole.AGENT,
                password_hash=hashed_password, ussd_pin_hash=pin_hash,
                trust_score=95, province="Mashonaland Central", district="Mazowe"
            )
            db.add(agent_user)
            db.flush()
            
            agent_profile = AgentProfile(
                user_id=agent_user.id, agent_code=f"ZT-{random.randint(100, 999)}",
                assigned_region="Mashonaland Central"
            )
            db.add(agent_profile)

        # 5. Diversified Listings
        listings_data = [
            {"farmer": farmers[0], "sector": Sector.CROPS, "type": "Tobacco (Flue-Cured)", "qty": 1200, "grade": "Export", "price": 4.25},
            {"farmer": farmers[1], "sector": Sector.CROPS, "type": "White Maize", "qty": 5000, "grade": "Grade A", "price": 335.0},
            {"farmer": farmers[2], "sector": Sector.LIVESTOCK, "type": "Cattle (Boran Steer)", "qty": 8, "grade": "Prime", "price": 1100.0},
            {"farmer": farmers[3], "sector": Sector.CROPS, "type": "Potatoes", "qty": 200, "grade": "Grade A", "price": 14.50},
        ]
        
        active_listings = []
        for l in listings_data:
            listing = db.query(Listing).filter(Listing.product_type == l["type"], Listing.seller_id == l["farmer"].id).first()
            if not listing:
                listing = Listing(
                    seller_id=l["farmer"].id, sector=l["sector"], product_type=l["type"],
                    quantity=l["qty"], grade=l["grade"], location_province=l["farmer"].province,
                    location_district=l["farmer"].district, price_per_unit=l["price"],
                    status=ListingStatus.ACTIVE, verification_status="verified"
                )
                db.add(listing)
                db.flush()
            active_listings.append(listing)

        # 6. SEED Offers & Deals
        if active_listings and buyers:
            offer1 = Offer(
                listing_id=active_listings[1].id, buyer_id=buyers[0].id, seller_id=active_listings[1].seller_id,
                quantity=1000, offered_price=330.0, status=OfferStatus.PENDING,
                buyer_message="Interested in a bulk purchase of this maize."
            )
            db.add(offer1)
            
            offer2 = Offer(
                listing_id=active_listings[0].id, buyer_id=buyers[2].id, seller_id=active_listings[0].seller_id,
                quantity=500, offered_price=4.20, status=OfferStatus.ACCEPTED,
                buyer_message="Ready for immediate procurement."
            )
            db.add(offer2)
            db.flush()
            
            order = Order(
                offer_id=offer2.id, listing_id=offer2.listing_id,
                buyer_id=offer2.buyer_id, seller_id=offer2.seller_id,
                order_number=f"AT-{random.randint(10000, 99999)}",
                quantity=offer2.quantity, total_amount=offer2.quantity * offer2.offered_price,
                platform_fee=offer2.quantity * offer2.offered_price * 0.05,
                seller_payout=(offer2.quantity * offer2.offered_price) * 0.95,
                status=OrderStatus.ESCROW_HELD
            )
            db.add(order)

        # 7. SEED Transactions
        history_users = farmers + buyers
        for i in range(25):
            random_user = random.choice(history_users)
            tx = Transaction(
                user_id=random_user.id,
                type=random.choice([TransactionType.PAYMENT, TransactionType.FEE, TransactionType.DEPOSIT]),
                amount=random.uniform(20, 1500),
                currency="USD",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(tx)

        db.commit()
        logger.info("Platform Governance Sync Successful.")
        
        return {
            "status": "success",
            "message": "Platform Governance Sync Complete.",
            "counts": {
                "farmers": len(farmers),
                "buyers": len(buyers),
                "listings": len(listings_data),
                "offers": 2,
                "orders": 1,
                "transactions": 25
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
