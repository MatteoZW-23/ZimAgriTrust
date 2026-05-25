"""Sync all missing columns across orders, offers, and agent_applications tables.

The SQLAlchemy models define columns that do not yet exist in the database.
This migration adds them using IF NOT EXISTS / existence checks to be idempotent.

Revision ID: 0040
Revises: 0039
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def _add_column_if_not_exists(conn, table: str, column: str, definition: str):
    """Helper: add a column only if it doesn't already exist."""
    result = conn.execute(text(
        f"SELECT 1 FROM information_schema.columns "
        f"WHERE table_name = '{table}' AND column_name = '{column}'"
    ))
    if not result.fetchone():
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def upgrade() -> None:
    conn = op.get_bind()

    # ── ORDERS table ─────────────────────────────────────────────────────────
    orders_cols = [
        ("quantity", "FLOAT DEFAULT 0"),
        ("platform_fee", "FLOAT DEFAULT 0"),
        ("seller_payout", "FLOAT DEFAULT 0"),
        ("currency", "VARCHAR(5) DEFAULT 'USD'"),
        ("logistics_type", "VARCHAR(20) DEFAULT 'PLATFORM'"),
        ("handover_code", "VARCHAR(10)"),
        ("transport_commission", "FLOAT DEFAULT 0"),
        ("driver_payout", "FLOAT DEFAULT 0"),
        ("transport_insurance_elected", "BOOLEAN DEFAULT FALSE"),
        ("transport_insurance_fee", "FLOAT DEFAULT 0"),
        ("refunded_amount", "FLOAT DEFAULT 0"),
        ("adjustment_memo", "TEXT"),
        ("fraud_risk_score", "FLOAT DEFAULT 0"),
        ("fraud_risk_level", "VARCHAR(20)"),
        ("fraud_flags", "JSONB"),
        ("ai_reviewed", "BOOLEAN DEFAULT FALSE"),
    ]
    for col, defn in orders_cols:
        _add_column_if_not_exists(conn, "orders", col, defn)

    # ── OFFERS table ─────────────────────────────────────────────────────────
    offers_cols = [
        ("currency", "VARCHAR(5) DEFAULT 'USD'"),
        ("logistics_type", "VARCHAR(20) DEFAULT 'PLATFORM'"),
        ("buyer_message", "TEXT"),
    ]
    for col, defn in offers_cols:
        _add_column_if_not_exists(conn, "offers", col, defn)

    # ── AGENT_APPLICATIONS table ─────────────────────────────────────────────
    app_cols = [
        ("first_name", "VARCHAR(100)"),
        ("last_name", "VARCHAR(100)"),
        ("email", "VARCHAR(255)"),
        ("address", "VARCHAR(500)"),
        ("next_of_kin", "VARCHAR(200)"),
        ("profile_photo", "VARCHAR(500)"),
        ("uploaded_documents", "JSONB DEFAULT '{}'::jsonb"),
        ("background_details", "VARCHAR(2000)"),
    ]
    for col, defn in app_cols:
        _add_column_if_not_exists(conn, "agent_applications", col, defn)

    # ── AGENT_TRAINING table (from 0028b that was skipped) ───────────────────
    _add_column_if_not_exists(conn, "agent_training", "final_exam_attempts", "INTEGER DEFAULT 0")


def downgrade() -> None:
    # Not dropping columns in downgrade to avoid data loss
    pass
