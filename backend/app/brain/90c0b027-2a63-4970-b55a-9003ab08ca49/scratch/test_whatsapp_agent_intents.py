import asyncio
import sys
import os
import uuid

# Ensure we can import from app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.services.whatsapp_service import WhatsAppService

async def test_whatsapp_agent_intents():
    db = SessionLocal()
    try:
        print("--- [TEST] WhatsApp Agent Intent Verification ---")
        
        # 1. Create/Find a test Agent
        test_phone = "263771112222"
        agent_user = db.query(User).filter(User.phone_number == test_phone).first()
        if not agent_user:
            agent_user = User(
                full_name="Test Field Agent",
                phone_number=test_phone,
                role=UserRole.AGENT,
                password_hash="...",
                trust_score=95
            )
            db.add(agent_user)
            db.commit()
            db.refresh(agent_user)
        
        # 2. Test 'tasks' intent
        print("Testing 'tasks' intent...")
        resp_tasks = await WhatsAppService.process_message(db, agent_user, "Check my tasks", False, None)
        
        if "Pending Field Tasks" in resp_tasks or "assigned verifications complete" in resp_tasks:
            print("[OK] Task intent handled correctly for Agent role.")
        else:
            print("[FAIL] Task intent failed.")

        # 3. Test 'earnings' intent
        print("Testing 'earnings' intent...")
        resp_earnings = await WhatsAppService.process_message(db, agent_user, "How much have I earned?", False, None)
        
        if "Agent Earnings Statement" in resp_earnings:
            print("[OK] Earnings intent handled correctly for Agent role.")
        else:
            print("[FAIL] Earnings intent failed.")

        # 4. Test 'location' intent
        print("Testing 'location' intent...")
        resp_loc = await WhatsAppService.process_message(db, agent_user, "Where is the next location?", False, None)
        
        if "Field Navigation" in resp_loc:
            print("[OK] Location intent handled correctly.")
        else:
            print("[FAIL] Location intent failed.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_whatsapp_agent_intents())
