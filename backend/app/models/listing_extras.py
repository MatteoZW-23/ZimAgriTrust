"""Listing-extras models — saved/favorited listings (F#92) and abuse reports (F#94)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SavedListing(Base):
    """A user has saved/favorited a listing.

    Spec: F#92 — Save listing (buyer functions §3.4).
    """

    __tablename__ = "saved_listings"
    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_saved_listing"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ListingReportReason(str, enum.Enum):
    FRAUD = "FRAUD"
    DUPLICATE = "DUPLICATE"
    INAPPROPRIATE = "INAPPROPRIATE"
    INACCURATE = "INACCURATE"
    PRICING = "PRICING"
    OTHER = "OTHER"


class ListingReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    UPHELD = "UPHELD"
    DISMISSED = "DISMISSED"


class ListingReport(Base):
    """A buyer/farmer reports a listing for review.

    Spec: F#94 — Report listing (buyer functions §3.4).
    """

    __tablename__ = "listing_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    reason: Mapped[ListingReportReason] = mapped_column(Enum(ListingReportReason), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ListingReportStatus] = mapped_column(
        Enum(ListingReportStatus), default=ListingReportStatus.OPEN, nullable=False
    )

    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
