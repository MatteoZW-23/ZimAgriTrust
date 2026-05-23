"""
Driver models for ZimAgriTrust transport/logistics system.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DriverStatus(str, enum.Enum):
    """Driver account status"""
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    UNDER_INVESTIGATION = "under_investigation"


class Driver(Base):
    """Driver profile linked to a User account"""
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Vehicle information
    vehicle_reg: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    vehicle_capacity_kg: Mapped[float] = mapped_column(Float, default=1000.0)
    vehicle_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # License information
    license_number: Mapped[str] = mapped_column(String(100), nullable=False)
    license_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Location/operating area
    current_district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status and verification
    status: Mapped[DriverStatus] = mapped_column(Enum(DriverStatus), default=DriverStatus.PENDING_REVIEW, nullable=False)
    insurance_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    background_cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance metrics
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Document paths (uploaded files)
    doc_national_id_front: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_national_id_back: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_license_front: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_license_back: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_vehicle_registration: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_vehicle_photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_profile_photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doc_live_selfie: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional fields (legacy compatibility)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="driver_profile")
    jobs = relationship("DriverJob", back_populates="driver", cascade="all, delete-orphan")


class DriverJobStatus(str, enum.Enum):
    """Status of a driver job/assignment"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    PICKUP_DONE = "pickup_done"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    PAID = "paid"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class DriverJob(Base):
    """Driver job/assignment for a specific order"""
    __tablename__ = "driver_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    
    # Job details
    status: Mapped[DriverJobStatus] = mapped_column(Enum(DriverJobStatus), default=DriverJobStatus.PENDING, nullable=False)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Pricing
    total_transport_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    driver_payout: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Rating
    buyer_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    driver = relationship("Driver", back_populates="jobs")
    order = relationship("Order", back_populates="driver_jobs")


class TransportScenario(str, enum.Enum):
    """Transport/logistics scenario types"""
    SELF_PICKUP = "self_pickup"
    PLATFORM_FLEET = "platform_fleet"
    FARMER_DELIVERY = "farmer_delivery"
    THIRD_PARTY = "third_party"
    AGGREGATED = "aggregated"
