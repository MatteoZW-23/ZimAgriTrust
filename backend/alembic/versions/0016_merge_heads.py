"""Merge alembic heads

Revision ID: 0016
Revises: 0015, add_notification_prefs
Create Date: 2026-05-01 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0016'
down_revision = ('0015', 'add_notification_prefs')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration, no actual schema changes
    pass


def downgrade():
    # This is a merge migration, no actual schema changes
    pass
