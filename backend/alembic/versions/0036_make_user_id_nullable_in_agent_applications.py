"""make user_id nullable in agent_applications

Revision ID: 0036
Revises: 0035
Create Date: 2026-05-23 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0036'
down_revision = '0035'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('agent_applications', 'user_id', nullable=True)


def downgrade():
    op.alter_column('agent_applications', 'user_id', nullable=False)
