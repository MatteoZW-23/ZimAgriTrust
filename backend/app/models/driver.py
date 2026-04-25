"""
AgriTrust Driver Model
Covers: driver registration, vehicle details, ratings, penalties, suspension.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DriverStatus(str, enum.Enum):
    PENDING_REVIEW  = "PENDING_REVIEW"   # Application submitted
    ACTIVE          = "ACTIVE"           # Cleared to take jobs
    SUSPENDED       = "SUSPENDED"        # Temporarily blocked
    TERMINATED      = "TERMINATED"       # Permanently removed
    RETRAINING      = "RETRAINING"       # Must complete retraining


class TransportScenario(str, enum.Enum):
    BUYER_COLLECTS   = "BUYER_COLLECTS"
    FARMER_DELIVERS  = "FARMER_DELIVERS"
    THIRD_PARTY      = "THIRD_PARTY"
    PLATFORM_FLEET   = "PLATFORM_FLEET"
    COOPERATIVE      = "COOPERATIVE"


class Driver(Base):
    """
    Registered third-party or platform driver.
    Linked to a User account for auth/wallet.
    """
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Vehicle
    vehicle_reg: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50))   # e.g. "3-Ton Truck", "Pickup"
    vehicle_capacity_kg: Mapped[float] = mapped_column(Float, default=1000.0)
    is_platform_fleet: Mapped[bool] = mapped_column(Boolean, default=False)

    # Compliance
    license_number: Mapped[str] = mapped_column(String(30), nullable=False)
    license_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    background_cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    # Performance
    status: Mapped[DriverStatus] = mapped_column(Enum(DriverStatus), default=DriverStatus.PENDING_REVIEW)
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=5.0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)

    # Location (for matching)
    current_district: Mapped[Optional[str]] = mapped_column(String(50))
    current_lat: Mapped[Optional[float]] = mapped_column(Float)
    current_lon: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    jobs = relationship("DriverJob", back_populates="driver")


class DriverJob(Base):
    """
    A single transport job assigned to a driver.
    Tracks fee, commission, payout, and rating.
    """
    __tablename__ = "driver_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)

    # Fees
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    base_fee: Mapped[float] = mapped_column(Float, default=7.0)       # $7 base
    distance_fee: Mapped[float] = mapped_column(Float, default=0.0)   # km × $0.50
    waiting_fee: Mapped[float] = mapped_column(Float, default=0.0)    # $2 per 30 min
    total_transport_fee: Mapped[float] = mapped_column(Float, default=0.0)
    platform_commission: Mapped[float] = mapped_column(Float, default=0.0)  # 10%
    driver_payout: Mapped[float] = mapped_column(Float, default=0.0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    # PENDING → ACCEPTED → PICKUP_DONE → DELIVERED → PAID

    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Rating
    buyer_rating: Mapped[Optional[int]] = mapped_column(Integer)       # 1-5
    buyer_rating_note: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="jobs")
    order  = relationship("Order",  foreign_keys=[order_id])
