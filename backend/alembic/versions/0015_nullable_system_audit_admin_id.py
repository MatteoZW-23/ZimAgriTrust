"""Allow system audits without a user-backed admin actor.

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "system_audits",
        "admin_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "system_audits",
        "admin_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
