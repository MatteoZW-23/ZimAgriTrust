import uuid
from sqlalchemy import create_engine, text
from app.db.base import Base
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.listing import Listing, Sector, ListingStatus
from app.core.security import get_password_hash

def recreate():
    engine = create_engine(settings.DATABASE_URL)
    print("Force-dropping all tables (CASCADE)...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
        
    print("Creating all tables from new models...")
    Base.metadata.create_all(bind=engine)   
    
    db = SessionLocal()
    print("Seeding new UUID data...")
    
    # MJ Admin
    admin_id = uuid.uuid4()
    admin = User(
        id=admin_id,
        full_name="MJ Admin",
        phone_number="+263771234567",
        password_hash=get_password_hash("1111"),
        role=UserRole.ADMIN,
        is_active=True,
        trust_score=100
    )
    db.add(admin)

    # Demo Farmer
    farmer_id = uuid.uuid4()
    farmer = User(
        id=farmer_id,
        full_name="Seed Farmer",
        phone_number="+263781234567",
        password_hash=get_password_hash("2222"),
        role=UserRole.FARMER,
        province="Mashonaland Central",
        district="Mazowe",
        trust_score=85
    )
    db.add(farmer)
    
    # Demo Buyer
    buyer_id = uuid.uuid4()
    buyer = User(
        id=buyer_id,
        full_name="Bulk Buyer",
        phone_number="+263791234567",
        password_hash=get_password_hash("3333"),
        role=UserRole.BUYER,
        province="Harare",
        trust_score=90
    )
    db.add(buyer)

    # Demo Agent
    agent_id = uuid.uuid4()
    agent = User(
        id=agent_id,
        full_name="Mash West Agent",
        phone_number="+263711234567",
        password_hash=get_password_hash("4444"),
        role=UserRole.AGENT,
        province="Mashonaland West",
        trust_score=95
    )
    db.add(agent)
    
    db.commit()
    
    # Removed Demo Listing block to allow pure 'zero-data' functional testing 
    # of the pipeline (listings, escrow, delivery).
    
    print(f"Success! Database reset. Admin: {admin_id}, Farmer: {farmer_id}, Buyer: {buyer_id}, Agent: {agent_id}")
    db.close()

if __name__ == "__main__":
    recreate()
