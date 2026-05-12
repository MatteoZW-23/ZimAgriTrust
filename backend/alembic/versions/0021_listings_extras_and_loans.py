"""Listings extras (saved/report/stats/photos/expiry) and loan module foundation.

Adds spec coverage for:
  - F#52  listing photos
  - F#56  listing stats (view_count)
  - F#58  expire listing (expires_at)
  - F#92  saved/favorite listings
  - F#94  report listing
  - F#337-348  loan module (loan_products, loans, loan_repayments)

Revision ID: 0021
Revises: 0020
Create Date: 2026-05-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0021"
down_revision = "0020"
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
LOAN_PURPOSE = sa.Enum(
    "INPUT", "EQUIPMENT", "EXPANSION", "EMERGENCY",
    name="loanpurpose",
)
LOAN_STATUS = sa.Enum(
    "DRAFT", "SUBMITTED", "AGENT_VERIFICATION", "APPROVED", "REJECTED",
    "DISBURSED", "ACTIVE", "REPAID", "DEFAULTED",
    name="loanstatus",
)


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # listings: new columns
    # ------------------------------------------------------------------
    op.add_column("listings", sa.Column("boosted_until", sa.DateTime(), nullable=True))
    op.add_column("listings", sa.Column(
        "view_count", sa.Integer(), nullable=False, server_default="0"
    ))
    op.add_column("listings", sa.Column("photo_urls", postgresql.JSON(), nullable=True))
    op.add_column("listings", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("listings", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_listings_expires_at", "listings", ["expires_at"])

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
    LISTING_REPORT_REASON.create(bind, checkfirst=True)
    LISTING_REPORT_STATUS.create(bind, checkfirst=True)
    op.create_table(
        "listing_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("reason", LISTING_REPORT_REASON, nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", LISTING_REPORT_STATUS, nullable=False, server_default="OPEN"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # loan_products  (F#339 catalog)
    # ------------------------------------------------------------------
    LOAN_PURPOSE.create(bind, checkfirst=True)
    LOAN_STATUS.create(bind, checkfirst=True)
    op.create_table(
        "loan_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("purpose", LOAN_PURPOSE, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_amount_usd", sa.Float(), nullable=False),
        sa.Column("max_amount_usd", sa.Float(), nullable=False),
        sa.Column("interest_rate_annual", sa.Float(), nullable=False),
        sa.Column("min_term_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_term_months", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("min_trust_score", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # loans  (F#337-344)
    # ------------------------------------------------------------------
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("loan_products.id"), nullable=False, index=True),
        sa.Column("amount_usd", sa.Float(), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("interest_rate_annual", sa.Float(), nullable=False),
        sa.Column("monthly_payment_usd", sa.Float(), nullable=False),
        sa.Column("purpose_text", sa.Text(), nullable=True),
        sa.Column("status", LOAN_STATUS, nullable=False, server_default="DRAFT"),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("agent_verified_purpose", sa.Boolean(), nullable=True),
        sa.Column("agent_assessed_viable", sa.Boolean(), nullable=True),
        sa.Column("agent_notes", sa.Text(), nullable=True),
        sa.Column("agent_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("disbursed_at", sa.DateTime(), nullable=True),
        sa.Column("next_due_date", sa.DateTime(), nullable=True),
        sa.Column("total_repaid_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("outstanding_principal_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ------------------------------------------------------------------
    # loan_repayments  (F#342)
    # ------------------------------------------------------------------
    op.create_table(
        "loan_repayments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount_usd", sa.Float(), nullable=False),
        sa.Column("principal_component_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("interest_component_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("paid_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("method", sa.String(40), nullable=False, server_default="WALLET"),
        sa.Column("reference", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("loan_repayments")
    op.drop_table("loans")
    op.drop_table("loan_products")
    LOAN_STATUS.drop(bind, checkfirst=True)
    LOAN_PURPOSE.drop(bind, checkfirst=True)

    op.drop_table("listing_reports")
    LISTING_REPORT_STATUS.drop(bind, checkfirst=True)
    LISTING_REPORT_REASON.drop(bind, checkfirst=True)

    op.drop_table("saved_listings")

    op.drop_index("ix_listings_expires_at", table_name="listings")
    op.drop_column("listings", "updated_at")
    op.drop_column("listings", "expires_at")
    op.drop_column("listings", "photo_urls")
    op.drop_column("listings", "view_count")
    op.drop_column("listings", "boosted_until")
