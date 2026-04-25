"""
Migration script to sync USSD PIN with existing user passwords.
This ensures all existing users can use USSD with their current password.
"""

from app.db.session import SessionLocal
from app.models.user import User


def sync_ussd_pins():
    """
    Update all users to have ussd_pin_hash matching their password_hash.
    This allows existing users to use USSD with their current password.
    """
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.ussd_pin_hash.is_(None)).all()
        
        count = 0
        for user in users:
            if user.password_hash:
                user.ussd_pin_hash = user.password_hash
                count += 1
        
        db.commit()
        print(f"✅ Successfully synced USSD PIN for {count} users")
        print(f"📱 Users can now use USSD with their existing password/PIN")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error syncing USSD PINs: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    sync_ussd_pins()
