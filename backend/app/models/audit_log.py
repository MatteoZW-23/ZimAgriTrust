from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from app.db.base_class import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True) # If performed by admin
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String) # CREATE_LISTING, REJECT_AGENT, OVERRIDE_DISPUTE
    resource_type = Column(String) # TRANSACTION, AGENT, MODEL
    resource_id = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
