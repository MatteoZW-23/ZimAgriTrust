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
    raised_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    resolved_by_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)  # Agent who resolved dispute
    
    type: Mapped[str] = mapped_column("dispute_type", String(30))
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="coredisputestatus"), default=DisputeStatus.OPEN
    )
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
    resolved_by_agent = relationship("Agent", foreign_keys=[resolved_by_agent_id])

    @property
    def product(self) -> str:
        return self.order.listing.product_type if self.order and self.order.listing else "Agricultural Goods"

    @property
    def amount(self) -> float:
        return self.order.total_amount if self.order else 0.0

    @property
    def buyer_name(self) -> str:
        return self.order.buyer.full_name if self.order and self.order.buyer else "N/A"

    @property
    def buyer_phone(self) -> str:
        return self.order.buyer.phone_number if self.order and self.order.buyer else "N/A"

    @property
    def buyer_trust(self) -> int:
        return self.order.buyer.trust_score if self.order and self.order.buyer else 50

    @property
    def seller_name(self) -> str:
        return self.order.seller.full_name if self.order and self.order.seller else "N/A"

    @property
    def seller_phone(self) -> str:
        return self.order.seller.phone_number if self.order and self.order.seller else "N/A"

    @property
    def seller_trust(self) -> int:
        return self.order.seller.trust_score if self.order and self.order.seller else 50

    @property
    def ai_risk(self) -> int:
        # Risk score derived from dispute status — replace with ML model output when available
        if self.status == DisputeStatus.OPEN:
            return 0
        return 0

    @property
    def ai_recommendation(self) -> str:
        """AI resolution suggestions based on case analysis"""
        if "quality" in self.description.lower() or "grade" in self.type.lower():
            return "Quality dispute detected. Recommend 15% discount or agent-led re-grading."
        if "quantity" in self.description.lower() or "shortage" in self.type.lower():
            return "Quantity discrepancy found. Suggest partial refund for missing weight."
        return "Manual audit required. Complex behavioral pattern detected."
