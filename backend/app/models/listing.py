import enum
import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, Date, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sector(str, enum.Enum):
    CROPS = "CROPS"
    LIVESTOCK = "LIVESTOCK"
    POULTRY = "POULTRY"
    DAIRY = "DAIRY"
    FISHERIES = "FISHERIES"
    VALUE_ADDED = "VALUE_ADDED"
    HORTICULTURE = "HORTICULTURE"
    AQUACULTURE = "AQUACULTURE"
    APICULTURE = "APICULTURE"
    SERICULTURE = "SERICULTURE"
    FLORICULTURE = "FLORICULTURE"
    VITICULTURE = "VITICULTURE"
    OLERICULTURE = "OLERICULTURE"
    POMOLOGY = "POMOLOGY"
    PISCICULTURE = "PISCICULTURE"
    MARICULTURE = "MARICULTURE"
    INPUTS = "INPUTS"
    MIXED_FARMING = "MIXED_FARMING"
    ARABLE_FARMING = "ARABLE_FARMING"
    PASTORAL_FARMING = "PASTORAL_FARMING"


class LogisticsType(str, enum.Enum):
    PLATFORM       = "PLATFORM"        # Third-party driver (default)
    SELF_COLLECT   = "SELF_COLLECT"    # Buyer picks up from farm
    SELF_DELIVER   = "SELF_DELIVER"    # Farmer delivers to buyer
    PLATFORM_FLEET = "PLATFORM_FLEET"  # ZimAgritrust-managed vehicle (premium)
    COOPERATIVE    = "COOPERATIVE"     # Shared farmer cooperative vehicle


class ListingStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SOLD = "SOLD"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class CropGrade(str, enum.Enum):
    GRADE_A = "GRADE_A"
    GRADE_B = "GRADE_B"
    GRADE_C = "GRADE_C"
    EXPORT = "EXPORT"


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

    @property
    def seller_name(self) -> str:
        return self.seller.full_name if self.seller else "Anonymous"

    @property
    def seller_trust_score(self) -> int:
        return self.seller.trust_score if self.seller else 0

    @property
    def seller_phone_masked(self) -> str:
        return self.seller.masked_phone if self.seller else "****"

    # AI Vision Fields
    ai_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ai_crop_type: Mapped[Optional[str]] = mapped_column(String(50))
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float)
    ai_grade_estimate: Mapped[Optional[str]] = mapped_column(String(10))
    ai_health_status: Mapped[Optional[str]] = mapped_column(String(100))
    ai_verification_level: Mapped[Optional[str]] = mapped_column(String(20))  # auto_approve, suggest_approve, flag_review, reject
    ai_raw_response: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Verification tracking
    verification_status: Mapped[str] = mapped_column(String(20), default="pending") # pending, verified, rejected
    verified_by_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agents.id"), nullable=True)  # Agent who verified
    verified_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)  # True if verified by AI
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_fee: Mapped[float] = mapped_column(Float, default=0.0)
    boosted_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # F#56 — listing stats (view tracking)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # F#52 — listing photos (URLs of uploaded images)
    photo_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # F#58 — auto-expire support
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    trade_sessions = relationship("TradeSession", back_populates="listing")


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COUNTERED = "COUNTERED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus), default=OfferStatus.PENDING)
    logistics_type: Mapped[LogisticsType] = mapped_column(Enum(LogisticsType), default=LogisticsType.PLATFORM)
    buyer_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    listing = relationship("Listing", back_populates="offers")
    buyer = relationship("User", back_populates="offers_made", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="offers_received", foreign_keys=[seller_id])
    order = relationship("Order", back_populates="offer", uselist=False)


class TradeSession(Base):
    __tablename__ = "trade_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(20), default="negotiating") # discovery, negotiating, committed, closed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    listing = relationship("Listing", back_populates="trade_sessions")
    messages = relationship("TradeMessage", back_populates="session", cascade="all, delete-orphan")


class TradeMessage(Base):
    __tablename__ = "trade_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trade_sessions.id"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_formal_offer: Mapped[bool] = mapped_column(Boolean, default=False)
    offer_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # {price, qty, currency}
    
    signature: Mapped[Optional[str]] = mapped_column(String(100)) # SHA-256 integrity hash
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("TradeSession", back_populates="messages")


class BuyerRequest(Base):
    __tablename__ = "buyer_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_required: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), default="kg")
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    delivery_location: Mapped[Optional[str]] = mapped_column(String(100))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    status: Mapped[str] = mapped_column(String(20), default="open") # open, filled, expired, cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    responses = relationship("FarmerResponse", back_populates="request", cascade="all, delete-orphan")


class FarmerResponse(Base):
    __tablename__ = "farmer_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("buyer_requests.id"), nullable=False, index=True)
    farmer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    supply_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    bid_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, accepted, declined
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    request = relationship("BuyerRequest", back_populates="responses")
    farmer = relationship("User", foreign_keys=[farmer_id])
