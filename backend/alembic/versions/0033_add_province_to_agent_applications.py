"""add province to agent_applications

Revision ID: 0033
Revises: 0032
Create Date: 2026-05-23 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0033'
down_revision = '0032'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('agent_applications', sa.Column('province', sa.String(50), nullable=True))
    op.add_column('agent_applications', sa.Column('district', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('agent_applications', 'district')
    op.drop_column('agent_applications', 'province')
