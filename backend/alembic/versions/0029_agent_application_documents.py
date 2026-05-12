"""Add documents to agent applications.

Revision ID: 0029
Revises: 0028
Create Date: 2026-05-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_applications", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("agent_applications", sa.Column("documents", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("agent_applications", sa.Column("references", postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_applications", "references")
    op.drop_column("agent_applications", "documents")
    op.drop_column("agent_applications", "email")
