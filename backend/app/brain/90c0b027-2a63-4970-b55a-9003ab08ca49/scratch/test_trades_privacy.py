import asyncio
import sys
import os
import uuid
from sqlalchemy.orm import Session

# Ensure we can import from app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.listing import Listing, TradeSession, TradeMessage, Sector
from app.models.transaction import Order, OrderStatus
from app.models.dispute import Dispute, DisputeStatus
from app.api.v1.endpoints.trades import get_session_messages

async def test_trades_privacy():
    db = SessionLocal()
    try:
        print("--- [TEST] Trades Privacy Verification ---")
        
        # 1. Setup Test Data
        farmer = User(full_name="Farmer Joe", phone_number=str(uuid.uuid4())[:15], role=UserRole.FARMER, password_hash="...", status="active")
        buyer = User(full_name="Buyer Bob", phone_number=str(uuid.uuid4())[:15], role=UserRole.BUYER, password_hash="...", status="active")
        agent = User(full_name="Agent Smith", phone_number=str(uuid.uuid4())[:15], role=UserRole.AGENT, password_hash="...", status="active")
        db.add_all([farmer, buyer, agent])
        db.commit()
        
        listing = Listing(seller_id=farmer.id, product_type="Maize", quantity=10, price_per_unit=400, sector=Sector.CROPS)
        db.add(listing)
        db.commit()
        
        session = TradeSession(listing_id=listing.id, buyer_id=buyer.id, seller_id=farmer.id)
        db.add(session)
        db.commit()

        order = Order(
            listing_id=listing.id,
            buyer_id=buyer.id,
            seller_id=farmer.id,
            total_amount=4000,
            status=OrderStatus.DISPUTED,
            order_number=f"TRX-{uuid.uuid4().hex[:8].upper()}"
        )
        db.add(order)
        db.commit()
        
        # 2. Test UNAUTHORIZED ACCESS (Agent not assigned to dispute)
        print("Testing unauthorized agent access...")
        try:
            get_session_messages(session.id, db, agent)
            print("[FAIL] Agent was able to access chat without dispute assignment.")
        except Exception as e:
            if "Negotiation Hub Privacy" in str(e):
                print(f"[OK] Agent access denied as expected: {str(e)[:50]}")
            else:
                print(f"[FAIL] Unexpected error: {e}")

        # 3. Test AUTHORIZED ACCESS (Agent assigned to dispute)
        print("Testing authorized agent access (after dispute assignment)...")
        dispute = Dispute(
             order_id=order.id,
             agent_assigned=agent.id,
             status=DisputeStatus.OPEN,
             raised_by=buyer.id,
             type="QUALITY",
             description="Poor quality maize"
        )
        db.add(dispute)
        db.commit()
        
        try:
            msgs = get_session_messages(session.id, db, agent)
            print("[OK] Agent successfully accessed chat after dispute assignment.")
        except Exception as e:
            print(f"[FAIL] Agent could not access chat even when assigned to dispute: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_trades_privacy())
