"""Add user_sessions table and security fields to users

Revision ID: 0020
Revises: 0019
Create Date: 2026-05-03 12:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('access_token_jti', sa.String(64), nullable=False, index=True),
        sa.Column('refresh_token_jti', sa.String(64), nullable=True),
        sa.Column('device_fingerprint', sa.String(128), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('geo_country', sa.String(2), nullable=True),
        sa.Column('geo_city', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoke_reason', sa.String(50), nullable=True),
    )

    # Add security columns to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False, nullable=True))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_history', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('must_change_password_reason', sa.String(50), nullable=True))


def downgrade():
    op.drop_column('users', 'must_change_password_reason')
    op.drop_column('users', 'password_history')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
    op.drop_table('user_sessions')
