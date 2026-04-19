import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class ListingVerificationReport(Base):
    __tablename__ = "listing_verification_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_assignments.id"), nullable=False)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)

    # Findings
    exists: Mapped[bool] = mapped_column(Boolean, default=True)
    verified_quantity: Mapped[float] = mapped_column(Float)
    matching_grade: Mapped[str] = mapped_column(String(20))
    
    # Evidence
    photos: Mapped[List[str]] = mapped_column(JSON) # List of URLs/Cloud storage paths
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    geo_timestamp: Mapped[datetime] = mapped_column(DateTime)

    # Observations
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assignment = relationship("AgentAssignment")
    listing = relationship("Listing")
    agent = relationship("Agent")


class DeliveryReport(Base):
    __tablename__ = "delivery_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_assignments.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)

    # Delivery Stats
    delivered_quantity: Mapped[float] = mapped_column(Float)
    quality_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Evidence
    handover_photos: Mapped[List[str]] = mapped_column(JSON)
    buyer_signature: Mapped[Optional[str]] = mapped_column(Text) # Base64 or path
    farmer_signature: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    discrepancy_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    assignment = relationship("AgentAssignment")
    order = relationship("Order")
    agent = relationship("Agent")
