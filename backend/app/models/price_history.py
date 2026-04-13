import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class PriceHistory(Base):
    """Historical price data for ML models"""
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_type = Column(String(50), nullable=False)
    grade = Column(String(20))
    location = Column(String(100))
    price_per_unit = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    source = Column(String(50))  # "transaction", "market_survey", etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
