import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Enum, Float, ForeignKey, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from app.models.listing import LogisticsType

class TripStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LogisticsTrip(Base):
    """
    Trip marketplace for Transporters to list their capacity.
    Example: '3-Ton truck from Lupane to Bulawayo on April 5th'
    """
    __tablename__ = "logistics_trips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Route details
    origin_district: Mapped[str] = mapped_column(String(50))
    destination_city: Mapped[str] = mapped_column(String(50))
    
    # Capacity tracking
    available_capacity_kg: Mapped[float] = mapped_column(Float)
    price_per_kg: Mapped[float] = mapped_column(Float) # Standardized shipping rate
    
    # Schedule
    departure_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[TripStatus] = mapped_column(Enum(TripStatus), default=TripStatus.PLANNED)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AggregationBooking(Base):
    """
    Link between an Order, a Listing, and a LogisticsTrip. 
    Tracks the 'Virtual Aggregation' of multiple smallholder harvests into one truck load.
    """
    __tablename__ = "aggregation_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("logistics_trips.id"))
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"))
    
    booked_quantity_kg: Mapped[float] = mapped_column(Float)
    pickup_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    trip = relationship("LogisticsTrip")
    listing = relationship("Listing")
