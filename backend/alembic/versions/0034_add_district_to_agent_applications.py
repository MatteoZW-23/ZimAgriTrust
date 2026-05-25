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
    conn = op.get_bind()
    conn.execute(sa.text(
        "ALTER TABLE agent_applications ADD COLUMN IF NOT EXISTS district VARCHAR(50)"
    ))


def downgrade():
    pass
