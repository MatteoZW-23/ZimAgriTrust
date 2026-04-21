from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.db.base_class import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="admin") # superadmin, auditor, support
    permissions = Column(JSON, default={})
    is_active = Column(Boolean(), default=True)
