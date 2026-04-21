#!/usr/bin/env python
"""
Initialize database with tables and default data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentSpecialization
from app.core.security import get_password_hash

def init_database():
    """Create all tables and seed default data"""
    print("📦 Initializing database...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin = db.query(User).filter(User.phone_number == "+2630000000").first()
        if not admin:
            admin = User(
                phone_number="+2630000000",
                full_name="System Administrator",
                password_hash=get_password_hash("AgriTrust@2026!"),
                role=UserRole.ADMIN,
                is_active=True,
                trust_score=100
            )
            db.add(admin)
            print("✅ Admin user created (Phone: +2630000000, Pass: AgriTrust@2026!)")
        
        # Database is now initialized with only the System Administrator.
        # Field agents will be onboarded via the recruitment pipeline.
        db.commit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()
