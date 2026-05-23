"""Migration 0016 - columns already exist in migration 0006

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columns already exist in migration 0006
    pass


def downgrade() -> None:
    # No columns added in this migration
    pass
