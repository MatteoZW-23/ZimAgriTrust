"""Supplier module.

Revision ID: 0032
Revises: 0031
Create Date: 2026-05-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


# Enums
supplier_business_type_enum = sa.Enum(
    "agro_dealer", "distributor", "manufacturer", "importer",
    name="supplierbusinesstype",
)
supplier_verification_status_enum = sa.Enum(
    "pending", "under_review", "approved", "rejected", "suspended",
    name="supplierverificationstatus",
)
supplier_product_type_enum = sa.Enum(
    "input", "machinery",
    name="supplierproducttype",
)
input_category_enum = sa.Enum(
    "seeds", "fertilizer", "pesticides", "herbicides", "fungicides", "animal_feed",
    name="supplierinputcategory",
)
machinery_category_enum = sa.Enum(
    "tractor", "sprayer", "irrigation", "tiller", "harvester", "tools",
    name="suppliermachinerycategory",
)
product_condition_enum = sa.Enum(
    "new", "used", "refurbished",
    name="supplierproductcondition",
)
supplier_product_status_enum = sa.Enum(
    "active", "out_of_stock", "draft", "expired", "suspended",
    name="supplierproductstatus",
)
supplier_order_status_enum = sa.Enum(
    "new", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded",
    name="supplierorderstatus",
)
supplier_payment_status_enum = sa.Enum(
    "pending", "escrow", "paid", "refunded",
    name="supplierpaymentstatus",
)
supplier_wallet_txn_type_enum = sa.Enum(
    "sale", "withdrawal", "platform_fee", "refund", "boost_fee", "adjustment",
    name="supplierwallettxntype",
)


def upgrade() -> None:
    # Create enums
    for e in (
        supplier_business_type_enum, supplier_verification_status_enum,
        supplier_product_type_enum, input_category_enum, machinery_category_enum,
        product_condition_enum, supplier_product_status_enum,
        supplier_order_status_enum, supplier_payment_status_enum,
        supplier_wallet_txn_type_enum,
    ):
        e.create(op.get_bind(), checkfirst=True)

    # Add SUPPLIER to UserRole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'supplier'")

    # supplier_profiles table
    op.create_table(
        "supplier_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("business_name", sa.String(200), nullable=False),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("tax_id", sa.String(100), nullable=True),
        sa.Column("business_type", supplier_business_type_enum, nullable=True),
        sa.Column("years_in_operation", sa.Integer(), nullable=True),
        sa.Column("physical_address", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("product_categories", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("verification_status", supplier_verification_status_enum, nullable=False, server_default="pending"),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_sales", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("available_balance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("pending_balance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("lifetime_earnings", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("shipping_policy", sa.Text(), nullable=True),
        sa.Column("return_policy", sa.Text(), nullable=True),
        sa.Column("business_hours", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_supplier_profiles_user_id", "supplier_profiles", ["user_id"])

    # supplier_documents table
    op.create_table(
        "supplier_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_profiles.id"), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_url", sa.String(500), nullable=False),
        sa.Column("document_name", sa.String(200), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_supplier_documents_supplier_id", "supplier_documents", ["supplier_id"])

    # supplier_products table
    op.create_table(
        "supplier_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_profiles.id"), nullable=False),
        sa.Column("sku", sa.String(50), nullable=True, unique=True),
        sa.Column("product_type", supplier_product_type_enum, nullable=False),
        sa.Column("input_category", input_category_enum, nullable=True),
        sa.Column("machinery_category", machinery_category_enum, nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(5), nullable=False, server_default="USD"),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_type", sa.String(20), nullable=False, server_default="piece"),
        sa.Column("min_stock_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("manufacturer", sa.String(200), nullable=True),
        sa.Column("safety_data_sheet_url", sa.String(500), nullable=True),
        sa.Column("condition", product_condition_enum, nullable=True),
        sa.Column("warranty_months", sa.Integer(), nullable=True),
        sa.Column("delivery_included", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_url", sa.String(500), nullable=True),
        sa.Column("photo_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", supplier_product_status_enum, nullable=False, server_default="draft"),
        sa.Column("is_boosted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("boost_fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("boosted_until", sa.DateTime(), nullable=True),
        sa.Column("scheduled_publish_at", sa.DateTime(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("order_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_supplier_products_supplier_id", "supplier_products", ["supplier_id"])
    op.create_index("ix_supplier_products_sku", "supplier_products", ["sku"])

    # supplier_orders table
    op.create_table(
        "supplier_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_number", sa.String(20), nullable=False, unique=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_profiles.id"), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tax_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("shipping_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("platform_fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(5), nullable=False, server_default="USD"),
        sa.Column("delivery_address", sa.Text(), nullable=True),
        sa.Column("delivery_phone", sa.String(20), nullable=True),
        sa.Column("shipping_method", sa.String(50), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("delivery_proof_url", sa.String(500), nullable=True),
        sa.Column("status", supplier_order_status_enum, nullable=False, server_default="new"),
        sa.Column("payment_status", supplier_payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("promo_code", sa.String(50), nullable=True),
        sa.Column("promo_discount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("buyer_notes", sa.Text(), nullable=True),
        sa.Column("supplier_notes", sa.Text(), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_supplier_orders_supplier_id", "supplier_orders", ["supplier_id"])
    op.create_index("ix_supplier_orders_buyer_id", "supplier_orders", ["buyer_id"])
    op.create_index("ix_supplier_orders_order_number", "supplier_orders", ["order_number"])

    # supplier_order_items table
    op.create_table(
        "supplier_order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_orders.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_products.id"), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
    )
    op.create_index("ix_supplier_order_items_order_id", "supplier_order_items", ["order_id"])
    op.create_index("ix_supplier_order_items_product_id", "supplier_order_items", ["product_id"])

    # supplier_stock_history table
    op.create_table(
        "supplier_stock_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_products.id"), nullable=False),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("quantity_before", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_supplier_stock_history_product_id", "supplier_stock_history", ["product_id"])

    # supplier_wallet_transactions table
    op.create_table(
        "supplier_wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_profiles.id"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_orders.id"), nullable=True),
        sa.Column("txn_type", supplier_wallet_txn_type_enum, nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("net_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(5), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("withdrawal_method", sa.String(50), nullable=True),
        sa.Column("reference", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_supplier_wallet_transactions_supplier_id", "supplier_wallet_transactions", ["supplier_id"])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index("ix_supplier_wallet_transactions_supplier_id", "supplier_wallet_transactions")
    op.drop_table("supplier_wallet_transactions")

    op.drop_index("ix_supplier_stock_history_product_id", "supplier_stock_history")
    op.drop_table("supplier_stock_history")

    op.drop_index("ix_supplier_order_items_product_id", "supplier_order_items")
    op.drop_index("ix_supplier_order_items_order_id", "supplier_order_items")
    op.drop_table("supplier_order_items")

    op.drop_index("ix_supplier_orders_order_number", "supplier_orders")
    op.drop_index("ix_supplier_orders_buyer_id", "supplier_orders")
    op.drop_index("ix_supplier_orders_supplier_id", "supplier_orders")
    op.drop_table("supplier_orders")

    op.drop_index("ix_supplier_products_sku", "supplier_products")
    op.drop_index("ix_supplier_products_supplier_id", "supplier_products")
    op.drop_table("supplier_products")

    op.drop_index("ix_supplier_documents_supplier_id", "supplier_documents")
    op.drop_table("supplier_documents")

    op.drop_index("ix_supplier_profiles_user_id", "supplier_profiles")
    op.drop_table("supplier_profiles")

    # Drop enums
    for e in (
        supplier_wallet_txn_type_enum, supplier_payment_status_enum,
        supplier_order_status_enum, supplier_product_status_enum,
        product_condition_enum, machinery_category_enum,
        input_category_enum, supplier_product_type_enum,
        supplier_verification_status_enum, supplier_business_type_enum,
    ):
        e.drop(op.get_bind(), checkfirst=True)

    # Note: Cannot remove enum value from PostgreSQL enum directly
    # The SUPPLIER value in userrole enum will remain
