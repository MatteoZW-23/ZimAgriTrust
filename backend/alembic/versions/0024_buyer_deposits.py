"""Buyer deposit subsystem.

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


deposit_channel_enum = sa.Enum(
    "ecocash", "onemoney", "bank_transfer", "cash_agent", name="depositchannel"
)
deposit_intent_status_enum = sa.Enum(
    "pending", "agent_held", "completed", "failed", "cancelled",
    "refund_requested", "refunded",
    name="depositintentstatus",
)
refund_status_enum = sa.Enum("pending", "approved", "rejected", "processed", name="refundstatus")
recurrence_enum = sa.Enum("weekly", "biweekly", "monthly", name="recurrencecadence")


def upgrade() -> None:
    deposit_channel_enum.create(op.get_bind(), checkfirst=True)
    deposit_intent_status_enum.create(op.get_bind(), checkfirst=True)
    refund_status_enum.create(op.get_bind(), checkfirst=True)
    recurrence_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payment_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("channel", deposit_channel_enum, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("last4", sa.String(8), nullable=True),
        sa.Column("token", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("extra", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payment_methods_user_id", "payment_methods", ["user_id"])

    op.create_table(
        "deposit_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("channel", deposit_channel_enum, nullable=False),
        sa.Column("payment_method_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_methods.id"), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), server_default="USD"),
        sa.Column("status", deposit_intent_status_enum, nullable=False, server_default="pending"),
        sa.Column("external_reference", sa.String(100), nullable=True, unique=True),
        sa.Column("nonce", sa.String(64), nullable=False, unique=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("agent_collected_at", sa.DateTime(), nullable=True),
        sa.Column("agent_reconciled_at", sa.DateTime(), nullable=True),
        sa.Column("agent_receipt_no", sa.String(64), nullable=True),
        sa.Column("bank_reference", sa.String(64), nullable=True),
        sa.Column("receipt_url", sa.String(255), nullable=True),
        sa.Column("refundable_until", sa.DateTime(), nullable=True),
        sa.Column("requires_id_verification", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id_verification_completed_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_deposit_intents_user_id", "deposit_intents", ["user_id"])
    op.create_index("ix_deposit_intents_channel", "deposit_intents", ["channel"])
    op.create_index("ix_deposit_intents_status", "deposit_intents", ["status"])
    op.create_index("ix_deposit_intents_created_at", "deposit_intents", ["created_at"])

    op.create_table(
        "auto_deposit_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("payment_method_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_methods.id"), nullable=False),
        sa.Column("threshold_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("topup_amount_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("daily_max_topups", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "recurring_deposit_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("payment_method_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_methods.id"), nullable=False),
        sa.Column("amount_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("cadence", recurrence_enum, nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recurring_deposit_schedules_next_run_at", "recurring_deposit_schedules", ["next_run_at"])
    op.create_index("ix_recurring_deposit_schedules_user_id", "recurring_deposit_schedules", ["user_id"])

    op.create_table(
        "deposit_refund_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deposit_intent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deposit_intents.id"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee", sa.Numeric(12, 2), server_default="0"),
        sa.Column("net_refund", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", refund_status_enum, nullable=False, server_default="pending"),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_deposit_refund_requests_user_id", "deposit_refund_requests", ["user_id"])
    op.create_index("ix_deposit_refund_requests_status", "deposit_refund_requests", ["status"])

    op.create_table(
        "deposit_limits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_tier", sa.String(20), nullable=False, unique=True),
        sa.Column("daily_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("weekly_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("per_transaction_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("id_verification_required_above", sa.Numeric(12, 2), nullable=False, server_default="1000"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Seed default deposit limits
    op.execute(
        """
        INSERT INTO deposit_limits
            (user_tier, daily_limit, weekly_limit, monthly_limit, per_transaction_limit, id_verification_required_above)
        VALUES
            ('unverified', 200.00,  500.00,  1000.00, 200.00,  500.00),
            ('verified',   2000.00, 8000.00, 20000.00, 2000.00, 1000.00),
            ('trusted',    10000.00,30000.00,100000.00,10000.00,1000.00)
        """
    )


def downgrade() -> None:
    op.drop_table("deposit_limits")
    op.drop_index("ix_deposit_refund_requests_status", table_name="deposit_refund_requests")
    op.drop_index("ix_deposit_refund_requests_user_id", table_name="deposit_refund_requests")
    op.drop_table("deposit_refund_requests")
    op.drop_index("ix_recurring_deposit_schedules_user_id", table_name="recurring_deposit_schedules")
    op.drop_index("ix_recurring_deposit_schedules_next_run_at", table_name="recurring_deposit_schedules")
    op.drop_table("recurring_deposit_schedules")
    op.drop_table("auto_deposit_rules")
    op.drop_index("ix_deposit_intents_created_at", table_name="deposit_intents")
    op.drop_index("ix_deposit_intents_status", table_name="deposit_intents")
    op.drop_index("ix_deposit_intents_channel", table_name="deposit_intents")
    op.drop_index("ix_deposit_intents_user_id", table_name="deposit_intents")
    op.drop_table("deposit_intents")
    op.drop_index("ix_payment_methods_user_id", table_name="payment_methods")
    op.drop_table("payment_methods")
    recurrence_enum.drop(op.get_bind(), checkfirst=True)
    refund_status_enum.drop(op.get_bind(), checkfirst=True)
    deposit_intent_status_enum.drop(op.get_bind(), checkfirst=True)
    deposit_channel_enum.drop(op.get_bind(), checkfirst=True)
