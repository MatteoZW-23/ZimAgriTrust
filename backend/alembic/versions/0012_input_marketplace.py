"""Input marketplace.

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-06
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import text
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


input_listing_status_enum = postgresql.ENUM(
    "pending_verification", "active", "rejected", "sold_out", "expired", "removed",
    name="inputlistingstatus",
    create_type=False,
)
input_offer_status_enum = postgresql.ENUM(
    "pending", "accepted", "rejected", "expired", "withdrawn", name="inputofferstatus",
    create_type=False,
)
input_order_status_enum = postgresql.ENUM(
    "pending", "escrow_held", "shipped", "delivered", "completed", "disputed", "refunded",
    name="inputorderstatus",
    create_type=False,
)
input_report_reason_enum = postgresql.ENUM(
    "fake", "expired", "mislabelled", "unregistered", "other", name="inputreportreason",
    create_type=False,
)
input_report_status_enum = postgresql.ENUM(
    "open", "investigating", "upheld", "dismissed", name="inputreportstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    # Create enum types with raw SQL and try/except to handle duplicates
    try:
        op.get_bind().execute(text("CREATE TYPE inputlistingstatus AS ENUM ('pending_verification', 'active', 'rejected', 'sold_out', 'expired', 'removed')"))
    except Exception:
        pass
    try:
        op.get_bind().execute(text("CREATE TYPE inputofferstatus AS ENUM ('pending', 'accepted', 'rejected', 'expired', 'withdrawn')"))
    except Exception:
        pass
    try:
        op.get_bind().execute(text("CREATE TYPE inputorderstatus AS ENUM ('pending', 'escrow_held', 'shipped', 'delivered', 'completed', 'disputed', 'refunded')"))
    except Exception:
        pass
    try:
        op.get_bind().execute(text("CREATE TYPE inputreportreason AS ENUM ('fake', 'expired', 'mislabelled', 'unregistered', 'other')"))
    except Exception:
        pass
    try:
        op.get_bind().execute(text("CREATE TYPE inputreportstatus AS ENUM ('open', 'investigating', 'upheld', 'dismissed')"))
    except Exception:
        pass

    op.create_table(
        "input_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requires_registration", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_expiry", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_agent_verification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_regulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_input_categories_slug", "input_categories", ["slug"])

    op.create_table(
        "input_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("input_categories.id"), nullable=False),
        sa.Column("product_name", sa.String(150), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="unit"),
        sa.Column("price_per_unit", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), server_default="USD"),
        sa.Column("min_order_quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("location", sa.String(120), nullable=True),
        sa.Column("province", sa.String(50), nullable=True),
        sa.Column("photos", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("documents", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("registration_number", sa.String(80), nullable=True),
        sa.Column("status", postgresql.ENUM(name="inputlistingstatus", create_type=False), nullable=False, server_default="pending_verification"),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("is_boosted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("boost_paid_until", sa.DateTime(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_input_listings_seller_id", "input_listings", ["seller_id"])
    op.create_index("ix_input_listings_category_id", "input_listings", ["category_id"])
    op.create_index("ix_input_listings_status", "input_listings", ["status"])
    op.create_index("ix_input_listings_brand", "input_listings", ["brand"])
    op.create_index("ix_input_listings_province", "input_listings", ["province"])
    op.create_index("ix_input_listings_expiry_date", "input_listings", ["expiry_date"])
    op.create_index("ix_input_listings_created_at", "input_listings", ["created_at"])

    op.create_table(
        "input_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("input_listings.id"), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("offered_price_per_unit", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), server_default="USD"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="inputofferstatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_input_offers_listing_id", "input_offers", ["listing_id"])
    op.create_index("ix_input_offers_buyer_id", "input_offers", ["buyer_id"])
    op.create_index("ix_input_offers_status", "input_offers", ["status"])

    op.create_table(
        "input_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("offer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("input_offers.id"), nullable=False, unique=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("input_listings.id"), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_number", sa.String(20), nullable=False, unique=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(12, 2), server_default="0"),
        sa.Column("escrow_fee", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("seller_payout", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), server_default="USD"),
        sa.Column("status", postgresql.ENUM(name="inputorderstatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("is_bulk", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("tracking_number", sa.String(80), nullable=True),
        sa.Column("shipped_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("review_rating", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_input_orders_seller_id", "input_orders", ["seller_id"])
    op.create_index("ix_input_orders_buyer_id", "input_orders", ["buyer_id"])
    op.create_index("ix_input_orders_status", "input_orders", ["status"])
    op.create_index("ix_input_orders_listing_id", "input_orders", ["listing_id"])

    op.create_table(
        "input_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("input_listings.id"), nullable=False),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", postgresql.ENUM(name="inputreportreason", create_type=False), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("evidence_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", postgresql.ENUM(name="inputreportstatus", create_type=False), nullable=False, server_default="open"),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_input_reports_listing_id", "input_reports", ["listing_id"])
    op.create_index("ix_input_reports_status", "input_reports", ["status"])

    op.create_table(
        "input_price_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("input_listings.id"), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("input_categories.id"), nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "listing_id", "category_id", "brand", name="uq_input_price_alert_target"),
    )
    op.create_index("ix_input_price_alerts_user_id", "input_price_alerts", ["user_id"])
    op.create_index("ix_input_price_alerts_listing_id", "input_price_alerts", ["listing_id"])

    # Seed 7 default categories
    op.execute(
        """
        INSERT INTO input_categories
            (slug, name, description, requires_registration, requires_expiry,
             requires_agent_verification, is_regulated, is_active)
        VALUES
            ('seeds', 'Seeds', 'Maize, soybeans, wheat, vegetable seeds',
             FALSE, TRUE, TRUE, FALSE, TRUE),
            ('fertilizers', 'Fertilizers', 'Compound, nitrogen, organic',
             TRUE, FALSE, TRUE, TRUE, TRUE),
            ('pesticides', 'Pesticides', 'Insecticides, fungicides, herbicides',
             TRUE, TRUE, TRUE, TRUE, TRUE),
            ('equipment', 'Equipment', 'Sprayers, irrigation, tillers',
             FALSE, FALSE, TRUE, FALSE, TRUE),
            ('tools', 'Tools', 'Hoes, shovels, pruning shears',
             FALSE, FALSE, FALSE, FALSE, TRUE),
            ('animal_feed', 'Animal feed', 'Layers, broilers, cattle, goats, pigs',
             FALSE, TRUE, TRUE, FALSE, TRUE),
            ('other', 'Other agricultural supplies', 'Other supplies',
             FALSE, FALSE, TRUE, FALSE, TRUE)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_input_price_alerts_listing_id", table_name="input_price_alerts")
    op.drop_index("ix_input_price_alerts_user_id", table_name="input_price_alerts")
    op.drop_table("input_price_alerts")
    op.drop_index("ix_input_reports_status", table_name="input_reports")
    op.drop_index("ix_input_reports_listing_id", table_name="input_reports")
    op.drop_table("input_reports")
    op.drop_index("ix_input_orders_listing_id", table_name="input_orders")
    op.drop_index("ix_input_orders_status", table_name="input_orders")
    op.drop_index("ix_input_orders_buyer_id", table_name="input_orders")
    op.drop_index("ix_input_orders_seller_id", table_name="input_orders")
    op.drop_table("input_orders")
    op.drop_index("ix_input_offers_status", table_name="input_offers")
    op.drop_index("ix_input_offers_buyer_id", table_name="input_offers")
    op.drop_index("ix_input_offers_listing_id", table_name="input_offers")
    op.drop_table("input_offers")
    for ix in (
        "ix_input_listings_created_at", "ix_input_listings_expiry_date",
        "ix_input_listings_province", "ix_input_listings_brand",
        "ix_input_listings_status", "ix_input_listings_category_id",
        "ix_input_listings_seller_id",
    ):
        op.drop_index(ix, table_name="input_listings")
    op.drop_table("input_listings")
    op.drop_index("ix_input_categories_slug", table_name="input_categories")
    op.drop_table("input_categories")
    for e in (
        sa.Enum(name="inputreportstatus"), sa.Enum(name="inputreportreason"),
        sa.Enum(name="inputorderstatus"), sa.Enum(name="inputofferstatus"),
        sa.Enum(name="inputlistingstatus"),
    ):
        e.drop(op.get_bind(), checkfirst=True)
