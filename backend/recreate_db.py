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
    
    print("Success! Database reset. All tables created. No seed data injected.")

def bootstrap_admin():
    from app.services.auth_service import register_user
    from app.schemas.auth import UserRegister
    import os

    db = SessionLocal()
    try:
        # Check if admin already exists
        admin_phone = "0888888888"
        existing = db.query(User).filter(User.phone_number == admin_phone).first()
        if existing:
            print(f"Admin {admin_phone} already exists. Skipping bootstrap.")
            return

        print(f"Bootstrapping first admin user ({admin_phone})...")
        payload = UserRegister(
            full_name="System Administrator",
            phone_number=admin_phone,
            password="admin-secure-pin-2026",
            role=UserRole.ADMIN,
            admin_secret=settings.ADMIN_BOOTSTRAP_TOKEN
        )
        register_user(db, payload)
        print("Admin user created successfully. Use phone '0888888888' and password 'admin-secure-pin-2026' for first login.")
    except Exception as e:
        print(f"Bootstrap failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    recreate()
    if os.getenv("BOOTSTRAP_ADMIN", "false").lower() == "true":
        bootstrap_admin()

