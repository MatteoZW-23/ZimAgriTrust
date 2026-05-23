"""financial hardening — add reference/idempotency columns and order payment fields

Adds columns required by the Phase 2-4 hardening patches:
  transactions.reference         — provider request_id for idempotency dedup
  transactions.status            — already exists in some builds, safe ADD IF NOT EXISTS
  orders.payment_reference       — stores the winning webhook request_id
  orders.payment_confirmed_at    — timestamp when payment was confirmed
  orders.delivered_at            — timestamp when order was marked delivered (7-day timer)
  orders.completed_at            — timestamp when escrow was released
  orders.refunded_at             — timestamp when refund was issued
  orders.settled_at              — timestamp when dispute was settled
  orders.payment_initiated (status enum value)
  orders.payment_failed   (status enum value)

Revision ID: 0025
Revises: 0024
Create Date: 2026-05-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name=:t AND column_name=:c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def upgrade():
    # ── transactions.reference ─────────────────────────────────────────────
    if not _column_exists("transactions", "reference"):
        op.add_column(
            "transactions",
            sa.Column("reference", sa.String(256), nullable=True),
        )
    # Index for idempotency check: SELECT ... WHERE reference=? AND status='completed'
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_transactions_reference "
        "ON transactions (reference) WHERE reference IS NOT NULL"
    ))

    # ── orders — payment tracking timestamps ──────────────────────────────
    for col_name, col_type in [
        ("payment_reference",    sa.String(256)),
        ("payment_confirmed_at", sa.DateTime(timezone=True)),
        ("delivered_at",         sa.DateTime(timezone=True)),
        ("completed_at",         sa.DateTime(timezone=True)),
        ("refunded_at",          sa.DateTime(timezone=True)),
        ("settled_at",           sa.DateTime(timezone=True)),
    ]:
        if not _column_exists("orders", col_name):
            op.add_column("orders", sa.Column(col_name, col_type, nullable=True))

    # ── orders — add missing OrderStatus enum values ─────────────────────
    # First create the orderstatus enum type if it doesn't exist
    # The orders table was originally created with status as String(20), not an enum
    # We need to create the enum type before we can add values to it
    try:
        op.execute(sa.text(
            "CREATE TYPE orderstatus AS ENUM ("
            "'PENDING', 'ESCROW_HELD', 'SHIPPED', 'DELIVERED', "
            "'COMPLETED', 'DISPUTED', 'REFUNDED', 'CANCELLED'"
            ")"
        ))
    except Exception:
        pass  # Type already exists

    # PostgreSQL requires ALTER TYPE ... ADD VALUE for enum extension.
    # Each ADD VALUE is idempotent with IF NOT EXISTS (Postgres 9.6+).
    for value in ("PAYMENT_INITIATED", "PAYMENT_FAILED"):
        op.execute(sa.text(
            f"DO $$ BEGIN "
            f"  ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS '{value}'; "
            f"EXCEPTION WHEN duplicate_object THEN NULL; "
            f"END $$"
        ))


def downgrade():
    # Remove only the columns added in this migration (enum values cannot be removed in PG)
    for col in [
        "payment_reference", "payment_confirmed_at", "delivered_at",
        "completed_at", "refunded_at", "settled_at",
    ]:
        if _column_exists("orders", col):
            op.drop_column("orders", col)

    op.execute(sa.text(
        "DROP INDEX IF EXISTS ix_transactions_reference"
    ))
    if _column_exists("transactions", "reference"):
        op.drop_column("transactions", "reference")
