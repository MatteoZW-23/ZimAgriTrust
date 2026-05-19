"""
Seed a test supplier account — ZimAgriTrust

Run inside the backend container:
    docker compose exec backend python -m scripts.seed_supplier
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole, UserStatus
from app.models.supplier import SupplierProfile, SupplierVerificationStatus, SupplierBusinessType
import uuid

def seed_supplier():
    db = SessionLocal()
    try:
        phone = "+263771234567"
        email = "test@supplier.co.zw"
        password = "Supplier123!"
        full_name = "Test Supplier"
        business_name = "Agro Inputs Ltd"
        
        # Check if exists
        existing = db.query(User).filter(User.phone_number == phone).first()
        if existing:
            print(f"Supplier with phone {phone} already exists")
            return
        
        # Create user
        password_hash = get_password_hash(password)
        user = User(
            full_name=full_name,
            phone_number=phone,
            email=email,
            password_hash=password_hash,
            ussd_pin_hash=password_hash,  # Same for PIN-based login
            role=UserRole.SUPPLIER,
            status=UserStatus.ACTIVE,  # Directly active for testing
            is_active=True,
            trust_score=60,
            is_phone_verified=True,
        )
        db.add(user)
        db.flush()
        
        # Create supplier profile
        profile = SupplierProfile(
            user_id=user.id,
            business_name=business_name,
            registration_number="REG123456",
            tax_id="TAX789",
            business_type=SupplierBusinessType.AGRO_DEALER,
            years_in_operation=5,
            physical_address="123 Farm Road, Harare",
            contact_person=full_name,
            phone=phone,
            email=email,
            product_categories=["seeds", "fertilizer"],
            verification_status=SupplierVerificationStatus.APPROVED,
            rating=4.5,
        )
        db.add(profile)
        db.commit()
        
        print(f"✓ Test supplier created:")
        print(f"  Phone: {phone}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Status: ACTIVE")
        print(f"  Verification: APPROVED")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_supplier()
