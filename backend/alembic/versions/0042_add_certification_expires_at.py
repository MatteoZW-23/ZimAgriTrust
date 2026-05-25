"""Add certification_expires_at to agent_training.

This column exists in the AgentTraining model but was never migrated.

Revision ID: 0042
Revises: 0041
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE agent_training "
        "ADD COLUMN IF NOT EXISTS certification_expires_at TIMESTAMPTZ NULL"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE agent_training "
        "DROP COLUMN IF EXISTS certification_expires_at"
    ))
