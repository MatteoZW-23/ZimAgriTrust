"""add district to agent_applications

Revision ID: 0034
Revises: 0033
Create Date: 2026-05-23 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0034'
down_revision = '0033'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('agent_applications', sa.Column('district', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('agent_applications', 'district')
