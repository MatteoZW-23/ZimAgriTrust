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
        admin = db.query(User).filter(User.phone == "admin").first()
        if not admin:
            admin = User(
                phone="admin",
                name="System Administrator",
                role=UserRole.ADMIN,
                is_verified=True,
                trust_score=100
            )
            db.add(admin)
            print("✅ Admin user created")
        
        # Create sample agents
        agents_data = [
            {"phone": "0771000001", "name": "John Doe", "province": "Harare", "district": "Harare East"},
            {"phone": "0771000002", "name": "Jane Smith", "province": "Bulawayo", "district": "Bulawayo Central"},
            {"phone": "0771000003", "name": "Tendai Moyo", "province": "Manicaland", "district": "Mutare"},
        ]
        
        for agent_data in agents_data:
            user = db.query(User).filter(User.phone == agent_data["phone"]).first()
            if not user:
                user = User(
                    phone=agent_data["phone"],
                    name=agent_data["name"],
                    role=UserRole.AGENT,
                    is_verified=True,
                    trust_score=75
                )
                db.add(user)
                db.flush()
                
                agent = Agent(
                    user_id=user.id,
                    agent_code=f"AGT{user.id:04d}",
                    specialization=AgentSpecialization.ALL,
                    province=agent_data["province"],
                    district=agent_data["district"],
                    is_available=True
                )
                db.add(agent)
        
        db.commit()
        print(f"✅ {len(agents_data)} agents created")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()
