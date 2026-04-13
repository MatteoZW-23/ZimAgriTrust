import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class SystemAudit(Base):
    """General security and administrative audit trail"""
    __tablename__ = "system_audits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    admin = relationship("User", foreign_keys=[admin_id])
    
    action = Column(String(50), nullable=False) # e.g., ESCROW_RELEASE, USER_SUSPENDED, SETTINGS_CHANGE
    target_type = Column(String(30)) # e.g., USER, ORDER, DISPUTE
    target_id = Column(UUID(as_uuid=True))
    details = Column(JSON) # Detailed diff or metadata
    note = Column(Text) # Custom reason provided by admin
    client_ip = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
