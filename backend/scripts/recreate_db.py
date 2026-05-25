import os
from sqlalchemy import create_engine, text
from app.db.base import Base
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole

def recreate():
    if os.getenv("ALLOW_DB_RECREATE", "false").lower() != "true":
        raise RuntimeError("Refusing to recreate the database unless ALLOW_DB_RECREATE=true")

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

    db = SessionLocal()
    try:
        # Check if admin already exists
        admin_phone = os.getenv("BOOTSTRAP_ADMIN_PHONE")
        admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
        if not admin_phone or not admin_password:
            raise RuntimeError("BOOTSTRAP_ADMIN_PHONE and BOOTSTRAP_ADMIN_PASSWORD are required")

        existing = db.query(User).filter(User.phone_number == admin_phone).first()
        if existing:
            print(f"Admin {admin_phone} already exists. Skipping bootstrap.")
            return

        print("Bootstrapping first admin user...")
        payload = UserRegister(
            full_name="System Administrator",
            phone_number=admin_phone,
            password=admin_password,
            role=UserRole.ADMIN,
            admin_secret=settings.ADMIN_BOOTSTRAP_TOKEN
        )
        register_user(db, payload)
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Bootstrap failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    recreate()
    if os.getenv("BOOTSTRAP_ADMIN", "false").lower() == "true":
        bootstrap_admin()

