"""Agent practical assessments + shadowing/supervised review tables.

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


PRACTICAL_TYPE_ENUM = postgresql.ENUM(
    "GRADING", "APP_NAVIGATION", "PHOTO_EVIDENCE", "DISPUTE_ROLEPLAY",
    name="practicaltesttype",
    create_type=False,
)
SHADOWING_STATUS_ENUM = postgresql.ENUM(
    "PENDING", "APPROVED", "NEEDS_REVISION",
    name="shadowingstatus",
    create_type=False,
)


def upgrade() -> None:
    # Create enum types with raw SQL and try/except to handle duplicates
    from sqlalchemy import text
    try:
        op.get_bind().execute(text("CREATE TYPE practicaltesttype AS ENUM ('GRADING', 'APP_NAVIGATION', 'PHOTO_EVIDENCE', 'DISPUTE_ROLEPLAY')"))
    except Exception:
        pass  # Type already exists
    try:
        op.get_bind().execute(text("CREATE TYPE shadowingstatus AS ENUM ('PENDING', 'APPROVED', 'NEEDS_REVISION')"))
    except Exception:
        pass  # Type already exists

    # ── academy_practical_assessments ──────────────────────────────────────
    op.create_table(
        "academy_practical_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("test_type", PRACTICAL_TYPE_ENUM, nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passing_score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluator_notes", sa.String(2000), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_practical_agent_test",
        "academy_practical_assessments",
        ["agent_id", "test_type"],
        unique=False,
    )

    # ── agent_shadowing_logs ──────────────────────────────────────────────
    op.create_table(
        "agent_shadowing_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("senior_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=False, index=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK to agent_assignments added later
        sa.Column("task_type", sa.String(50), nullable=True),
        sa.Column("observation_notes", sa.String(2000), nullable=True),
        sa.Column("agent_actions", sa.String(2000), nullable=True),
        sa.Column("senior_feedback", sa.String(2000), nullable=True),
        sa.Column("status", SHADOWING_STATUS_ENUM, nullable=False, server_default="PENDING"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── agent_supervised_reviews ──────────────────────────────────────────
    op.create_table(
        "agent_supervised_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK to agent_assignments added later
        sa.Column("submission", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("review_notes", sa.String(2000), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agent_supervised_reviews")
    op.drop_table("agent_shadowing_logs")
    op.drop_index("ix_practical_agent_test", table_name="academy_practical_assessments")
    op.drop_table("academy_practical_assessments")
    SHADOWING_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    PRACTICAL_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
