"""Merge migration heads

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-01 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration, no actual schema changes
    pass


def downgrade():
    # This is a merge migration, no actual schema changes
    pass
