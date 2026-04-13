import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, DateTime, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PROPOSED_OFFER = "proposed_offer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    raised_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    agent_assigned: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    type: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.OPEN)
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Financial Resolution Data
    proposed_discount: Mapped[Optional[float]] = mapped_column(Float, default=0.0) # Percentage (0-100)
    proposed_refund_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0) # Absolute USD
    
    # Acceptance Tracking
    buyer_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    seller_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_resolution_memo: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="disputes")
    raised_by_user = relationship("User", foreign_keys=[raised_by])
    assigned_agent = relationship("User", foreign_keys=[agent_assigned])
