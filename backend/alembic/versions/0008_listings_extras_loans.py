"""Listings extras (saved/report/photos).

Adds spec coverage for:
  - F#52  listing photos
  - F#92  saved/favorite listings
  - F#94  report listing

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


# Enum names — created at upgrade, dropped at downgrade.
LISTING_REPORT_REASON = sa.Enum(
    "FRAUD", "DUPLICATE", "INAPPROPRIATE", "INACCURATE", "PRICING", "OTHER",
    name="listingreportreason",
)
LISTING_REPORT_STATUS = sa.Enum(
    "OPEN", "UNDER_REVIEW", "UPHELD", "DISMISSED",
    name="listingreportstatus",
)


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # listings: new columns
    # ------------------------------------------------------------------
    op.add_column("listings", sa.Column("boosted_until", sa.DateTime(), nullable=True))
    op.add_column("listings", sa.Column("photo_urls", postgresql.JSON(), nullable=True))

    # ------------------------------------------------------------------
    # saved_listings  (F#92)
    # ------------------------------------------------------------------
    op.create_table(
        "saved_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_saved_listing"),
    )

    # ------------------------------------------------------------------
    # listing_reports  (F#94)
    # ------------------------------------------------------------------
    # Create enum types explicitly using raw SQL with try/except to handle duplicates
    from sqlalchemy import text
    try:
        bind.execute(text("CREATE TYPE listingreportreason AS ENUM ('FRAUD', 'DUPLICATE', 'INAPPROPRIATE', 'INACCURATE', 'PRICING', 'OTHER')"))
    except Exception:
        pass  # Type already exists
    try:
        bind.execute(text("CREATE TYPE listingreportstatus AS ENUM ('OPEN', 'UNDER_REVIEW', 'UPHELD', 'DISMISSED')"))
    except Exception:
        pass  # Type already exists
    op.create_table(
        "listing_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("reason", postgresql.ENUM(name="listingreportreason", create_type=False), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="listingreportstatus", create_type=False), nullable=False, server_default="OPEN"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("listing_reports")
    LISTING_REPORT_STATUS.drop(bind, checkfirst=True)
    LISTING_REPORT_REASON.drop(bind, checkfirst=True)

    op.drop_table("saved_listings")

    op.drop_column("listings", "photo_urls")
    op.drop_column("listings", "boosted_until")
