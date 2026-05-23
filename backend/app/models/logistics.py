import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Enum, Float, ForeignKey, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from app.models.listing import LogisticsType


class TripStatus(str, enum.Enum):
    PLANNED    = "planned"
    IN_TRANSIT = "in_transit"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"


class DeliveryStatus(str, enum.Enum):
    """Full 9-state delivery lifecycle per ZimAgritrust spec."""
    PENDING_PICKUP          = "PENDING_PICKUP"
    PICKUP_SCHEDULED        = "PICKUP_SCHEDULED"
    PICKUP_IN_PROGRESS      = "PICKUP_IN_PROGRESS"
    PICKUP_COMPLETED        = "PICKUP_COMPLETED"
    IN_TRANSIT              = "IN_TRANSIT"
    DELAYED                 = "DELAYED"
    ARRIVED                 = "ARRIVED"
    DELIVERY_IN_PROGRESS    = "DELIVERY_IN_PROGRESS"
    DELIVERED               = "DELIVERED"
    CONFIRMED               = "CONFIRMED"
    AUTO_CONFIRMED          = "AUTO_CONFIRMED"
    DISPUTED                = "DISPUTED"


class DeliveryMethod(str, enum.Enum):
    BUYER_COLLECTS   = "BUYER_COLLECTS"    # Buyer comes to farm
    FARMER_DELIVERS  = "FARMER_DELIVERS"   # Farmer brings to buyer
    THIRD_PARTY      = "THIRD_PARTY"       # External driver


class OrderDelivery(Base):
    """
    Tracks the full delivery lifecycle for a single order.
    One-to-one with Order. Created when offer is accepted.
    """
    __tablename__ = "order_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True, index=True)

    # Method & Status
    method: Mapped[Optional[DeliveryMethod]] = mapped_column(Enum(DeliveryMethod), nullable=True)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING_PICKUP)

    # Scheduling
    pickup_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_arrival_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Inspection window — buyer has this long to confirm or dispute
    inspection_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Location
    pickup_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pickup_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Agent & Driver
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    driver_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_reg: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Photo evidence (list of URLs/paths)
    pickup_photos: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    delivery_photos: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # GPS stamps
    pickup_gps_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_gps_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order  = relationship("Order",  foreign_keys=[order_id])
    agent  = relationship("User",   foreign_keys=[agent_id])
    driver = relationship("User",   foreign_keys=[driver_id])


class LogisticsTrip(Base):
    """
    Trip marketplace for Drivers to list their capacity.
    Example: '3-Ton truck from Lupane to Bulawayo on April 5th'
    """
    __tablename__ = "logistics_trips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    origin_district: Mapped[str] = mapped_column(String(50))
    destination_city: Mapped[str] = mapped_column(String(50))

    available_capacity_kg: Mapped[float] = mapped_column(Float)
    price_per_kg: Mapped[float] = mapped_column(Float)

    departure_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[TripStatus] = mapped_column(Enum(TripStatus), default=TripStatus.PLANNED)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AggregationBooking(Base):
    """
    Links an Order/Listing to a LogisticsTrip for virtual aggregation.
    """
    __tablename__ = "aggregation_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("logistics_trips.id"))
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"))

    booked_quantity_kg: Mapped[float] = mapped_column(Float)
    pickup_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    trip    = relationship("LogisticsTrip")
    listing = relationship("Listing")
