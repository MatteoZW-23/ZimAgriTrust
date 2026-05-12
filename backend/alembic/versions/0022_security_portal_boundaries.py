"""Security portal boundaries and safer account closure.

Revision ID: 0022
Revises: 0021
Create Date: 2026-05-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=15),
        type_=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(length=32),
        type_=sa.String(length=15),
        existing_nullable=False,
    )
