import enum
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Enum, Float, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    FARMER = "farmer"
    BUYER = "buyer"
    AGENT = "agent"
    ADMIN = "admin"
    TRANSPORTER = "transporter"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    FLAGGED = "flagged"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class SubscriptionTier(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    
    # Core Identity (KYC Foundation)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    
    # Verification & Trust (KYC)
    national_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    id_document_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Secure link to ID
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Location Data (Verified via GPS)
    province: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_location_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Intelligence Scoring
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, default=50) # 0-100 (high is riskier)
    
    # Status Management
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Legacy support
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    status_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Balance & Wallet (Agri-Telecom Marketplace Specs)
    balance_usd: Mapped[float] = mapped_column(Float, default=0.0)
    balance_zig: Mapped[float] = mapped_column(Float, default=0.0)
    pending_usd: Mapped[float] = mapped_column(Float, default=0.0)
    pending_zig: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Monetization Tiers
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.BASIC)
    subscription_expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # USSD & Localization
    ussd_pin_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en") # en, sn, nd

    # Relationships
    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False)
    agent_profile = relationship("AgentProfile", back_populates="user", uselist=False)
    transporter_profile = relationship("TransporterProfile", back_populates="user", uselist=False)
    
    listings = relationship("Listing", back_populates="seller")
    offers_made = relationship("Offer", back_populates="buyer", foreign_keys="Offer.buyer_id")
    offers_received = relationship("Offer", back_populates="seller", foreign_keys="Offer.seller_id")
    orders_as_buyer = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    orders_as_seller = relationship("Order", back_populates="seller", foreign_keys="Order.seller_id")

    @property
    def masked_phone(self) -> str:
        """Returns a partially hidden phone number (e.g. +26377****003)"""
        if not self.phone_number:
            return ""
        if len(self.phone_number) <= 7:
            return "*" * len(self.phone_number)
        return f"{self.phone_number[:6]}****{self.phone_number[-3:]}"



class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="farmer_profile")
    
    farm_name: Mapped[Optional[str]] = mapped_column(String(100))
    farm_size_hectares: Mapped[float] = mapped_column(Float, default=0.0)
    primary_crops: Mapped[Optional[str]] = mapped_column(String(255)) # Comma separated
    production_scale: Mapped[str] = mapped_column(String(20), default="SMALLHOLDER")


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="buyer_profile")
    
    company_name: Mapped[Optional[str]] = mapped_column(String(100))
    procurement_focus: Mapped[Optional[str]] = mapped_column(String(255))
    buyer_tier: Mapped[str] = mapped_column(String(20), default="STANDARD")


class AgentProfile(Base):
    __tablename__ = "agent_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="agent_profile")
    
    assigned_zone: Mapped[Optional[str]] = mapped_column(String(50))
    verification_count: Mapped[int] = mapped_column(Integer, default=0)
    agent_level: Mapped[int] = mapped_column(Integer, default=1)


class TransporterProfile(Base):
    __tablename__ = "transporter_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="transporter_profile")
    
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50))
    carrying_capacity_kg: Mapped[float] = mapped_column(Float, default=0.0)
    operating_district: Mapped[Optional[str]] = mapped_column(String(50))
