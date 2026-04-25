"""add notification_prefs column to users

Revision ID: add_notification_prefs
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_notification_prefs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('notification_prefs', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'notification_prefs')
