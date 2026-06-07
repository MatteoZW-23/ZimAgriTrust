"""
Input marketplace — agricultural inputs (seeds, fertilizers, pesticides,
equipment, tools, animal feed, other).

Tables:
- input_categories       : 7 default categories with verification rules
- input_listings         : seller-created product listings
- input_offers           : buyer offers on a listing
- input_orders           : accepted offers → orders (escrow + delivery tracking)
- input_reports          : fake / expired / suspicious input reports
- input_price_alerts     : buyer alerts when listing price drops
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _enum_values(enum_cls):
    return [member.value for member in enum_cls]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InputListingStatus(str, enum.Enum):
    pending_verification = "pending_verification"
    active = "active"
    rejected = "rejected"
    sold_out = "sold_out"
    expired = "expired"
    removed = "removed"


class InputOfferStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"
    withdrawn = "withdrawn"


class InputOrderStatus(str, enum.Enum):
    pending = "pending"
    escrow_held = "escrow_held"
    shipped = "shipped"
    delivered = "delivered"
    completed = "completed"
    disputed = "disputed"
    refunded = "refunded"


class InputReportReason(str, enum.Enum):
    fake = "fake"
    expired = "expired"
    mislabelled = "mislabelled"
    unregistered = "unregistered"
    other = "other"


class InputReportStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    upheld = "upheld"
    dismissed = "dismissed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class InputCategory(Base):
    __tablename__ = "input_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    requires_registration: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_expiry: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_agent_verification: Mapped[bool] = mapped_column(Boolean, default=True)
    is_regulated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InputListing(Base):
    __tablename__ = "input_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("input_categories.id"), nullable=False, index=True)

    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="unit")  # kg, L, bag, piece
    price_per_unit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    min_order_quantity: Mapped[float] = mapped_column(Float, default=1)

    location: Mapped[Optional[str]] = mapped_column(String(120))
    province: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    photos: Mapped[Optional[List]] = mapped_column(JSON, default=list)        # list[str]
    documents: Mapped[Optional[List]] = mapped_column(JSON, default=list)     # registration certs, COA

    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(80))

    status: Mapped[InputListingStatus] = mapped_column(
        Enum(InputListingStatus, values_callable=_enum_values), default=InputListingStatus.pending_verification, nullable=False, index=True
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_paid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    view_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = relationship("User", foreign_keys=[seller_id])
    category = relationship("InputCategory")


class InputOffer(Base):
    __tablename__ = "input_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("input_listings.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    offered_price_per_unit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    note: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[InputOfferStatus] = mapped_column(
        Enum(InputOfferStatus, values_callable=_enum_values), default=InputOfferStatus.pending, nullable=False, index=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class InputOrder(Base):
    __tablename__ = "input_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("input_offers.id"), nullable=False, unique=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("input_listings.id"), nullable=False, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    escrow_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    seller_payout: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")

    status: Mapped[InputOrderStatus] = mapped_column(
        Enum(InputOrderStatus, values_callable=_enum_values), default=InputOrderStatus.pending, nullable=False, index=True
    )

    is_bulk: Mapped[bool] = mapped_column(Boolean, default=False)

    delivery_address: Mapped[Optional[str]] = mapped_column(Text)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(80))
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    review_rating: Mapped[Optional[int]] = mapped_column(Integer)
    review_text: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class InputReport(Base):
    __tablename__ = "input_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("input_listings.id"), nullable=False, index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    reason: Mapped[InputReportReason] = mapped_column(Enum(InputReportReason, values_callable=_enum_values), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    evidence_urls: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    status: Mapped[InputReportStatus] = mapped_column(
        Enum(InputReportStatus, values_callable=_enum_values), default=InputReportStatus.open, nullable=False, index=True
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class InputPriceAlert(Base):
    __tablename__ = "input_price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("input_listings.id"), index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("input_categories.id"))
    brand: Mapped[Optional[str]] = mapped_column(String(100))

    target_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", "category_id", "brand",
                         name="uq_input_price_alert_target"),
    )


class InputSavedSearch(Base):
    __tablename__ = "input_saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    query_text: Mapped[Optional[str]] = mapped_column(String(200))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("input_categories.id"))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[Optional[str]] = mapped_column(String(50))
    min_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    max_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    notify_on_match: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
