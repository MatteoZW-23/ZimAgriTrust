"""Add persistent notifications log table.

Revision ID: 0026
Revises: 0025
Create Date: 2026-05-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── notifications ───────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),           # sms | whatsapp | email | push
        sa.Column("event_type", sa.String(100), nullable=True),        # e.g. ORDER_CONFIRMED
        sa.Column("reference_id", sa.String(36), nullable=True),       # order/listing/dispute id
        sa.Column("reference_type", sa.String(50), nullable=True),     # 'order' | 'listing' | etc.
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),  # PENDING | SENT | FAILED | READ
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_notifications_user_id_created_at", "notifications", ["user_id", "created_at"])
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index("ix_notifications_reference_id", "notifications", ["reference_id"])

    # ── notification_preferences ────────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("order_updates", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("price_alerts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("promotional", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dispute_updates", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("payment_updates", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),   # Hour 0-23
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=sa.func.now()),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_reference_id", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_event_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id_created_at", table_name="notifications")
    op.drop_table("notifications")
