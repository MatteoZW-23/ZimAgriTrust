import uuid
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class TrustAudit(Base):
    """Audit trail for trust score calculations"""
    __tablename__ = "trust_audits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Note: Using transactions.id or orders.id depending on what's available
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    previous_score = Column(Float)
    new_score = Column(Float)
    delta = Column(Float)
    reason = Column(String(100))
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
