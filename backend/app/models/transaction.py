import enum
import uuid
from datetime import datetime
from typing import Optional, Any, Dict

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Import at module level to avoid circular import issues
from app.models.listing import LogisticsType


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"  # Added: payment flow started
    ESCROW_HELD = "ESCROW_HELD"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    CANCELLED = "REFUNDED"   # alias — maps to REFUNDED in DB
    SETTLED = "SETTLED"      # Resolved via agent mediation
    DISPUTED = "DISPUTED"
    PAYMENT_FAILED = "PAYMENT_FAILED"  # Added: for failed payment attempts


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

    # Payment tracking fields (referenced in payment_service.py)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    payment_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Logistics Tracking
    logistics_type: Mapped[LogisticsType] = mapped_column(Enum(LogisticsType), default=LogisticsType.PLATFORM)
    handover_code: Mapped[Optional[str]] = mapped_column(String(10))

    # Transport fee (added to order total when 3rd party / platform fleet)
    transport_fee: Mapped[float] = mapped_column(Float, default=0.0)
    transport_commission: Mapped[float] = mapped_column(Float, default=0.0)  # Platform's cut
    driver_payout: Mapped[float] = mapped_column(Float, default=0.0)         # Driver's net

    # Optional transport insurance (buyer-elected, flat $1.50 fee)
    transport_insurance_elected: Mapped[bool] = mapped_column(Boolean, default=False)
    transport_insurance_fee: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Post-Mediation Adjustments
    refunded_amount: Mapped[float] = mapped_column(Float, default=0.0) # For settlements
    adjustment_memo: Mapped[Optional[str]] = mapped_column(Text)
    
    # Agent Service Tracking
    fulfilled_by_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agents.id"), nullable=True)  # Agent who fulfilled order
    field_support_by_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agents.id"), nullable=True)  # Agent who provided field support
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # AI Fraud Detection
    fraud_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    fraud_risk_level: Mapped[Optional[str]] = mapped_column(String(20))  # low, medium, high
    fraud_flags: Mapped[Optional[dict]] = mapped_column(JSON)  # List of flags
    ai_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    offer = relationship("Offer", back_populates="order")
    listing = relationship("Listing", back_populates="orders")
    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="orders_as_seller", foreign_keys=[seller_id])
    disputes = relationship("Dispute", back_populates="order")
    
    @property
    def product(self) -> str:
        """Helper for frontend UI consistency"""
        return self.listing.product_type if self.listing else "Agricultural Goods"

    @property
    def seller_contact_reveal(self) -> str:
        """Reveals full seller phone only if escrow is funded."""
        if self.status in [OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.COMPLETED, OrderStatus.SETTLED]:
            return self.seller.phone_number if self.seller else "Not Available"
        return self.seller.masked_phone if self.seller else "****"

    @property
    def buyer_contact_reveal(self) -> str:
        """Reveals full buyer phone only if escrow is funded."""
        if self.status in [OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.COMPLETED, OrderStatus.SETTLED]:
            return self.buyer.phone_number if self.buyer else "Not Available"
        return self.buyer.masked_phone if self.buyer else "****"



class TransactionType(str, enum.Enum):
    PAYMENT = "PAYMENT"
    ESCROW_HOLD = "ESCROW_HOLD"
    ESCROW_RELEASE = "ESCROW_RELEASE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT" # Specialized for discounted settlements
    FEE = "FEE"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"


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

    ledger_entries = relationship("LedgerEntry", back_populates="transaction")


class TransportSurvey(Base):
    """
    Post-delivery survey capturing off-platform transport data.
    Submitted by buyer after confirming receipt.
    Used to understand transport patterns and identify partner opportunities.
    """
    __tablename__ = "transport_surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # How did goods move?
    transport_method: Mapped[Optional[str]] = mapped_column(String(50))
    # e.g. "own_vehicle", "friend_family", "local_taxi", "cooperative", "platform_driver"

    transport_cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    would_use_platform_transport: Mapped[Optional[bool]] = mapped_column(Boolean)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order = relationship("Order", foreign_keys=[order_id])
