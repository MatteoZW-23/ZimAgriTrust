import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class AgentSpecialization(str, enum.Enum):
    # Core Operations
    VERIFICATION = "verification"
    DISPUTE_RESOLUTION = "dispute_resolution"
    FIELD_SUPPORT = "field_support"
    
    # Industry Specializations
    GRAIN_INSPECTOR = "grain_inspector"
    LIVESTOCK_VETERINARY = "livestock_veterinary"
    COLD_CHAIN_LOGISTICS = "cold_chain_logistics"
    FISHERY_QUALITY = "fishery_quality"
    
    MANAGEMENT = "management"
    ALL = "all"


class AgentStatus(str, enum.Enum):
    TRAINEE = "trainee"
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"

    SUSPENDED = "suspended"


class Agent(Base):
    """Extended agent profile linked to User table"""
    __tablename__ = "agents"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    
    # Agent details
    agent_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[AgentSpecialization] = mapped_column(SQLEnum(AgentSpecialization), default=AgentSpecialization.ALL)
    status: Mapped[AgentStatus] = mapped_column(SQLEnum(AgentStatus), default=AgentStatus.ACTIVE)
    
    # Coverage & Performance
    province: Mapped[Optional[str]] = mapped_column(String(50))
    district: Mapped[Optional[str]] = mapped_column(String(50))
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    current_load: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    avg_response_time: Mapped[float] = mapped_column(Float, default=24.0) # hours
    
    # Financial Tracking
    wallet_balance: Mapped[float] = mapped_column(Float, default=0.0) # Realized earnings
    pending_earnings: Mapped[float] = mapped_column(Float, default=0.0) # Escrowed for completion
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="agent")
    assignments = relationship("AgentAssignment", back_populates="agent")


class AgentAssignment(Base):
    """Track agent assignments to listings, orders, disputes"""
    __tablename__ = "agent_assignments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    
    assignment_type: Mapped[str] = mapped_column(String(20)) # listing, order, dispute
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("listings.id"), nullable=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"), nullable=True)
    dispute_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("disputes.id"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="assigned") 
    priority: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timestamps
    assigned_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)
    deadline = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes & Results
    agent_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)

    # Bounty tracking
    bounty_amount: Mapped[float] = mapped_column(Float, default=0.0)
    bonus_amount: Mapped[float] = mapped_column(Float, default=0.0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    
    agent = relationship("Agent", back_populates="assignments")
