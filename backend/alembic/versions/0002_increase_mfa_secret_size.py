"""Increase mfa_secret column size for encrypted values

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-01 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Increase mfa_secret column size from 64 to 255 to accommodate Fernet encrypted values
    op.alter_column('users', 'mfa_secret',
               existing_type=sa.String(length=64),
               type_=sa.String(length=255),
               existing_nullable=True)


def downgrade():
    # Revert mfa_secret column size back to 64
    op.alter_column('users', 'mfa_secret',
               existing_type=sa.String(length=255),
               type_=sa.String(length=64),
               existing_nullable=True)
