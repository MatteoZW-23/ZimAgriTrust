# Monkeypatch passlib to support bcrypt 4.0+ (MUST BE AT THE VERY TOP)
try:
    import bcrypt as _orig_bcrypt
    from passlib.handlers.bcrypt import bcrypt as _passlib_bcrypt
    if not hasattr(_passlib_bcrypt, "__about__"):
        class _About:
            __version__ = getattr(_orig_bcrypt, "__version__", "4.0.0")
        _passlib_bcrypt.__about__ = _About()
except Exception:
    pass

from app.db.base import Base
from app.db.session import SessionLocal
# Import models to register them
from app.models.dispute import Dispute
from app.models.listing import Listing, Offer
from app.models.transaction import Transaction
from app.models.user import User
from app.services.sync_service import sync_system_data

def run_seed():
    db = SessionLocal()
    from app.db.session import engine
    try:
        print("--- Resetting Database Schema ---")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        result = sync_system_data(db)
        print("--- System Initialization Successful ---")
        print(f"Results: {result}")
        print("Verified accounts: Farmer (+263771000001), Buyer (+263771000002)")
        print("Access PIN: 1234")
    except Exception as e:
        print("Seed failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
