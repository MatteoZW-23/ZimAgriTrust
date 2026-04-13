import enum
import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, Date, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sector(str, enum.Enum):
    CROPS = "crops"
    LIVESTOCK = "livestock"
    POULTRY = "poultry"
    DAIRY = "dairy"
    FISHERIES = "fisheries"
    VALUE_ADDED = "value_added"


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class CropGrade(str, enum.Enum):
    GRADE_A = "grade_a"
    GRADE_B = "grade_b"
    GRADE_C = "grade_c"
    EXPORT = "export"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Product Details
    sector: Mapped[Sector] = mapped_column(Enum(Sector), nullable=False)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_subtype: Mapped[Optional[str]] = mapped_column(String(50))
    grade: Mapped[Optional[str]] = mapped_column(String(20))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), default="kg")
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    # Location (GPS Enforced)
    location_province: Mapped[Optional[str]] = mapped_column(String(50))
    location_district: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_location_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    pickup_address: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status & Visibility
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.ACTIVE)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending") # pending, verified, rejected
    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_fee: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Agricultural Details & Quality Logistics
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    storage_requirements: Mapped[Optional[str]] = mapped_column(String(100)) # e.g., "Cold Storage", "Ambient", "Dry"
    
    crop: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    data_records: Mapped[Optional[dict]] = mapped_column(JSON)
    
    @property
    def product(self):
        return self.product_type
    
    @product.setter
    def product(self, value):
        self.product_type = value
    
    # Relationships
    seller = relationship("User", back_populates="listings")
    offers = relationship("Offer", back_populates="listing", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="listing")


class OfferStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COUNTERED = "countered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    offered_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus), default=OfferStatus.PENDING)
    buyer_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    listing = relationship("Listing", back_populates="offers")
    buyer = relationship("User", back_populates="offers_made", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="offers_received", foreign_keys=[seller_id])
    order = relationship("Order", back_populates="offer", uselist=False)
