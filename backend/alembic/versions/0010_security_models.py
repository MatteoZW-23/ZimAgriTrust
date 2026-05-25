"""Security subsystem: super_admins, admin_approvals, audit_checksums,
fraud_alerts, withdrawal_limits, admin_action_logs.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


# Enums
approval_status_enum = sa.Enum(
    "pending", "partial_approved", "fully_approved", "rejected", "expired",
    name="approvalstatus",
)
approval_action_enum = sa.Enum(
    "refund", "large_transaction", "escrow_release", "escrow_override", "limit_override",
    name="approvalaction",
)
fraud_severity_enum = sa.Enum("low", "medium", "high", "critical", name="fraudseverity")
fraud_alert_type_enum = sa.Enum(
    "velocity", "structuring", "new_user_large_withdrawal", "duplicate_bank_details",
    "trust_score_spike", "limit_breach_attempt", "signature_mismatch",
    "unauthorized_override", "emergency_shutdown",
    name="fraudalerttype",
)
user_tier_enum = sa.Enum("unverified", "verified", "trusted", name="usertier")


def upgrade() -> None:
    # super_admins
    op.create_table(
        "super_admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("hardware_mfa_secret", sa.String(255), nullable=True),
        sa.Column("yubikey_public_id", sa.String(64), nullable=True),
        sa.Column("public_key", sa.Text(), nullable=True),
        sa.Column("ip_whitelist", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("phone_number", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_ip", sa.String(45), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("super_admins.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_super_admins_username", "super_admins", ["username"])
    op.create_index("ix_super_admins_email", "super_admins", ["email"])

    # admin_approvals
    from sqlalchemy import text
    bind = op.get_bind()
    try:
        bind.execute(text("CREATE TYPE approvalstatus AS ENUM ('pending', 'partial_approved', 'fully_approved', 'rejected', 'expired')"))
    except Exception:
        pass
    try:
        bind.execute(text("CREATE TYPE approvalaction AS ENUM ('refund', 'large_transaction', 'escrow_release', 'escrow_override', 'limit_override')"))
    except Exception:
        pass
    op.create_table(
        "admin_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("action", postgresql.ENUM(name="approvalaction", create_type=False), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(5), server_default="USD"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_by_1", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at_1", sa.DateTime(), nullable=True),
        sa.Column("signature_1", sa.String(128), nullable=True),
        sa.Column("approved_by_2", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at_2", sa.DateTime(), nullable=True),
        sa.Column("signature_2", sa.String(128), nullable=True),
        sa.Column("status", postgresql.ENUM(name="approvalstatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("fully_approved_at", sa.DateTime(), nullable=True),
        sa.Column("rules_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_admin_approvals_resource_id", "admin_approvals", ["resource_id"])
    op.create_index("ix_admin_approvals_status", "admin_approvals", ["status"])

    # audit_checksums
    op.create_table(
        "audit_checksums",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("table_name", sa.String(64), nullable=False),
        sa.Column("record_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(16), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("previous_checksum", sa.String(64), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=True),
        sa.Column("actor_role", sa.String(32), nullable=True),
        sa.Column("payload_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_checksums_table_name", "audit_checksums", ["table_name"])
    op.create_index("ix_audit_checksums_record_id", "audit_checksums", ["record_id"])
    op.create_index("ix_audit_checksums_checksum", "audit_checksums", ["checksum"])
    op.create_index("ix_audit_checksums_created_at", "audit_checksums", ["created_at"])

    # fraud_alerts
    try:
        bind.execute(text("CREATE TYPE fraudseverity AS ENUM ('low', 'medium', 'high', 'critical')"))
    except Exception:
        pass
    try:
        bind.execute(text("CREATE TYPE fraudalerttype AS ENUM ('velocity', 'structuring', 'new_user_large_withdrawal', 'duplicate_bank_details', 'trust_score_spike', 'limit_breach_attempt', 'signature_mismatch', 'unauthorized_override', 'emergency_shutdown')"))
    except Exception:
        pass
    op.create_table(
        "fraud_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("alert_type", postgresql.ENUM(name="fraudalerttype", create_type=False), nullable=False),
        sa.Column("severity", postgresql.ENUM(name="fraudseverity", create_type=False), nullable=False),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("related_resource_type", sa.String(50), nullable=True),
        sa.Column("related_resource_id", sa.String(64), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolved_by", sa.Integer(), sa.ForeignKey("super_admins.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("notified_super_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fraud_alerts_user_id", "fraud_alerts", ["user_id"])
    op.create_index("ix_fraud_alerts_alert_type", "fraud_alerts", ["alert_type"])
    op.create_index("ix_fraud_alerts_severity", "fraud_alerts", ["severity"])
    op.create_index("ix_fraud_alerts_resolved", "fraud_alerts", ["resolved"])
    op.create_index("ix_fraud_alerts_created_at", "fraud_alerts", ["created_at"])

    # withdrawal_limits
    try:
        bind.execute(text("CREATE TYPE usertier AS ENUM ('unverified', 'verified', 'trusted')"))
    except Exception:
        pass
    op.create_table(
        "withdrawal_limits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_tier", postgresql.ENUM(name="usertier", create_type=False), nullable=False, unique=True),
        sa.Column("daily_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("weekly_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("per_transaction_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("min_trust_score", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("super_admins.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # admin_action_logs
    op.create_table(
        "admin_action_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_kind", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("actor_level", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(5), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("signature", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_action_logs_actor_id", "admin_action_logs", ["actor_id"])
    op.create_index("ix_admin_action_logs_action", "admin_action_logs", ["action"])
    op.create_index("ix_admin_action_logs_resource_id", "admin_action_logs", ["resource_id"])
    op.create_index("ix_admin_action_logs_created_at", "admin_action_logs", ["created_at"])

    # Seed default withdrawal limits - REMOVED FOR PRODUCTION
    # Withdrawal limits should be configured via admin panel or separate seed script


def downgrade() -> None:
    op.drop_index("ix_admin_action_logs_created_at", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_resource_id", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_action", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_actor_id", table_name="admin_action_logs")
    op.drop_table("admin_action_logs")

    op.drop_table("withdrawal_limits")
    user_tier_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_fraud_alerts_created_at", table_name="fraud_alerts")
    op.drop_index("ix_fraud_alerts_resolved", table_name="fraud_alerts")
    op.drop_index("ix_fraud_alerts_severity", table_name="fraud_alerts")
    op.drop_index("ix_fraud_alerts_alert_type", table_name="fraud_alerts")
    op.drop_index("ix_fraud_alerts_user_id", table_name="fraud_alerts")
    op.drop_table("fraud_alerts")
    fraud_alert_type_enum.drop(op.get_bind(), checkfirst=True)
    fraud_severity_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_audit_checksums_created_at", table_name="audit_checksums")
    op.drop_index("ix_audit_checksums_checksum", table_name="audit_checksums")
    op.drop_index("ix_audit_checksums_record_id", table_name="audit_checksums")
    op.drop_index("ix_audit_checksums_table_name", table_name="audit_checksums")
    op.drop_table("audit_checksums")

    op.drop_index("ix_admin_approvals_status", table_name="admin_approvals")
    op.drop_index("ix_admin_approvals_resource_id", table_name="admin_approvals")
    op.drop_table("admin_approvals")
    approval_action_enum.drop(op.get_bind(), checkfirst=True)
    approval_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_super_admins_email", table_name="super_admins")
    op.drop_index("ix_super_admins_username", table_name="super_admins")
    op.drop_table("super_admins")
