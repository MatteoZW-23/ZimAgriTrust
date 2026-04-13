import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ESCROW_HELD = "escrow_held"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    SETTLED = "settled" # Resolved via agent mediation
    DISPUTED = "disputed"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("offers.id"), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Float, default=0.0)
    seller_payout: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Logistics Tracking
    from app.models.logistics import LogisticsType
    logistics_type: Mapped[LogisticsType] = mapped_column(Enum(LogisticsType), default=LogisticsType.PLATFORM)
    handover_code: Mapped[Optional[str]] = mapped_column(String(10)) # For Self-Logistics verification
    
    # Post-Mediation Adjustments
    refunded_amount: Mapped[float] = mapped_column(Float, default=0.0) # For settlements
    adjustment_memo: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    offer = relationship("Offer", back_populates="order")
    listing = relationship("Listing", back_populates="orders")
    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="orders_as_seller", foreign_keys=[seller_id])
    disputes = relationship("Dispute", back_populates="order")


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    ESCROW_HOLD = "escrow_hold"
    ESCROW_RELEASE = "escrow_release"
    REFUND = "refund"
    ADJUSTMENT = "adjustment" # Specialized for discounted settlements
    FEE = "fee"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="completed") # pending, completed, failed
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
