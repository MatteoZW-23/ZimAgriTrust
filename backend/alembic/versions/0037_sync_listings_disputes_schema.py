"""Synchronize listings and disputes tables with ORM models.

Adds all columns defined in the SQLAlchemy models that are missing from the
database tables.  Also migrates data from legacy column names to new ones.

Missing listings columns: product_type, product_subtype, grade, quantity,
    quantity_unit, price_per_unit, currency, latitude, longitude,
    is_location_verified, pickup_address, ai_*, verification_*, is_boosted,
    boost_fee, is_perishable, expiry_date, harvest_date, storage_requirements,
    crop, location, notes, data_records

Missing disputes columns: type, resolved_by_agent_id, resolution,
    proposed_discount, proposed_refund_amount, buyer_accepted,
    seller_accepted, agent_resolution_memo

Revision ID: 0037
Revises: 0036
Create Date: 2026-05-24
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def _add(conn, table: str, col: str, definition: str) -> None:
    try:
        conn.execute(text(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {definition}"
        ))
        conn.commit()
    except Exception:
        conn.rollback()


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # LISTINGS — add columns the ORM model expects
    # ------------------------------------------------------------------
    listings_cols = [
        ("product_type",          "VARCHAR(50) NOT NULL DEFAULT ''"),
        ("product_subtype",       "VARCHAR(50)"),
        ("grade",                 "VARCHAR(20)"),
        ("quantity",              "FLOAT NOT NULL DEFAULT 0"),
        ("quantity_unit",         "VARCHAR(20) DEFAULT 'kg'"),
        ("price_per_unit",        "FLOAT NOT NULL DEFAULT 0"),
        ("currency",              "VARCHAR(5) DEFAULT 'USD'"),
        ("latitude",              "FLOAT"),
        ("longitude",             "FLOAT"),
        ("is_location_verified",  "BOOLEAN DEFAULT FALSE"),
        ("pickup_address",        "TEXT"),
        ("ai_verified",           "BOOLEAN DEFAULT FALSE"),
        ("ai_verified_at",        "TIMESTAMP"),
        ("ai_crop_type",          "VARCHAR(50)"),
        ("ai_confidence",         "FLOAT"),
        ("ai_grade_estimate",     "VARCHAR(10)"),
        ("ai_health_status",      "VARCHAR(100)"),
        ("ai_verification_level", "VARCHAR(20)"),
        ("ai_raw_response",       "JSON"),
        ("verification_status",   "VARCHAR(20) DEFAULT 'pending'"),
        ("verified_by_agent_id",  "UUID REFERENCES agents(id)"),
        ("verified_by_ai",        "BOOLEAN DEFAULT FALSE"),
        ("verification_notes",    "TEXT"),
        ("is_boosted",            "BOOLEAN DEFAULT FALSE"),
        ("boost_fee",             "FLOAT DEFAULT 0.0"),
        ("is_perishable",         "BOOLEAN DEFAULT FALSE"),
        ("expiry_date",           "DATE"),
        ("harvest_date",          "DATE"),
        ("storage_requirements",  "VARCHAR(100)"),
        ("crop",                  "VARCHAR(50)"),
        ("location",              "VARCHAR(200)"),
        ("notes",                 "TEXT"),
        ("data_records",          "JSON"),
    ]

    for col, defn in listings_cols:
        _add(conn, "listings", col, defn)

    # Migrate legacy data: crop_type -> product_type & crop
    try:
        conn.execute(text("""
            UPDATE listings
               SET product_type = crop_type,
                   crop         = crop_type
             WHERE product_type = ''
               AND crop_type IS NOT NULL
        """))
        conn.commit()
    except Exception:
        conn.rollback()

    # Migrate legacy data: quantity_kg -> quantity
    try:
        conn.execute(text("""
            UPDATE listings
               SET quantity = quantity_kg
             WHERE quantity = 0
               AND quantity_kg IS NOT NULL
        """))
        conn.commit()
    except Exception:
        conn.rollback()

    # Migrate legacy data: price_per_kg -> price_per_unit
    try:
        conn.execute(text("""
            UPDATE listings
               SET price_per_unit = price_per_kg
             WHERE price_per_unit = 0
               AND price_per_kg IS NOT NULL
        """))
        conn.commit()
    except Exception:
        conn.rollback()

    # ------------------------------------------------------------------
    # DISPUTES — add columns the ORM model expects
    # ------------------------------------------------------------------
    disputes_cols = [
        ("type",                    "VARCHAR(30)"),
        ("resolved_by_agent_id",    "UUID REFERENCES agents(id)"),
        ("resolution",              "VARCHAR(50)"),
        ("proposed_discount",       "FLOAT DEFAULT 0.0"),
        ("proposed_refund_amount",  "FLOAT DEFAULT 0.0"),
        ("buyer_accepted",          "BOOLEAN DEFAULT FALSE"),
        ("seller_accepted",         "BOOLEAN DEFAULT FALSE"),
        ("agent_resolution_memo",   "TEXT"),
    ]

    for col, defn in disputes_cols:
        _add(conn, "disputes", col, defn)

    # Migrate legacy data: dispute_type -> type
    try:
        conn.execute(text("""
            UPDATE disputes
               SET type = dispute_type
             WHERE type IS NULL
               AND dispute_type IS NOT NULL
        """))
        conn.commit()
    except Exception:
        conn.rollback()


def downgrade() -> None:
    conn = op.get_bind()

    # Drop disputes columns
    for col in [
        "type", "resolved_by_agent_id", "resolution",
        "proposed_discount", "proposed_refund_amount",
        "buyer_accepted", "seller_accepted", "agent_resolution_memo",
    ]:
        try:
            conn.execute(text(f"ALTER TABLE disputes DROP COLUMN IF EXISTS {col}"))
            conn.commit()
        except Exception:
            conn.rollback()

    # Drop listings columns
    for col in [
        "product_type", "product_subtype", "grade", "quantity", "quantity_unit",
        "price_per_unit", "currency", "latitude", "longitude",
        "is_location_verified", "pickup_address",
        "ai_verified", "ai_verified_at", "ai_crop_type", "ai_confidence",
        "ai_grade_estimate", "ai_health_status", "ai_verification_level",
        "ai_raw_response", "verification_status", "verified_by_agent_id",
        "verified_by_ai", "verification_notes",
        "is_boosted", "boost_fee",
        "is_perishable", "expiry_date", "harvest_date", "storage_requirements",
        "crop", "location", "notes", "data_records",
    ]:
        try:
            conn.execute(text(f"ALTER TABLE listings DROP COLUMN IF EXISTS {col}"))
            conn.commit()
        except Exception:
            conn.rollback()
