import enum
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Enum, Float, Integer, String, Text, ForeignKey, JSON, DateTime, func
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
    
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Verification & Trust (KYC)
    national_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    id_document_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Secure link to ID
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    id_verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Phone Verification
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Email Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Password Security
    password_changed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # list of previous hashes
    must_change_password_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'expired', 'breached', 'admin_reset'
    
    # Location Data (Verified via GPS)
    province: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_location_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    location_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Buyer Business Verification
    business_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    business_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Agent Verification Stages
    background_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    background_verified_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    training_completed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    practical_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    practical_passed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shadowing_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    shadowing_complete_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Intelligence Scoring
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, default=50) # 0-100 (high is riskier)
    
    # Status Management
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Legacy support
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    status_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Activity Tracking (for inactivity penalties)
    last_activity_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
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

    # Force PIN change on first login (set when system provisions account)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notification Preferences
    notification_prefs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

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


class TrustScoreEvent(Base):
    """Audit trail for all trust score changes"""
    __tablename__ = "trust_score_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    previous_score: Mapped[int] = mapped_column(Integer, nullable=False)
    new_score: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # system, admin, buyer, farmer, agent
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())



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
