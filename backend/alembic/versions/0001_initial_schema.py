"""Initial schema - create base tables

Revision ID: 0001
Revises: 
Create Date: 2026-05-20 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phone_number', sa.String(32), unique=True, index=True, nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('national_id', sa.String(20), unique=True, nullable=True),
        sa.Column('id_document_url', sa.String(255), nullable=True),
        sa.Column('id_verified', sa.Boolean(), default=False),
        sa.Column('id_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id_verification_notes', sa.Text(), nullable=True),
        sa.Column('is_phone_verified', sa.Boolean(), default=False),
        sa.Column('phone_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), default=False),
        sa.Column('mfa_secret', sa.String(64), nullable=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(255), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_history', postgresql.JSONB(), nullable=True),
        sa.Column('must_change_password_reason', sa.String(50), nullable=True),
        sa.Column('province', sa.String(50), nullable=True),
        sa.Column('district', sa.String(50), nullable=True),
        sa.Column('ward', sa.String(20), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_location_verified', sa.Boolean(), default=False),
        sa.Column('location_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('business_verified', sa.Boolean(), default=False),
        sa.Column('business_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('background_verified', sa.Boolean(), default=False),
        sa.Column('background_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed', sa.Boolean(), default=False),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('practical_passed', sa.Boolean(), default=False),
        sa.Column('practical_passed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shadowing_complete', sa.Boolean(), default=False),
        sa.Column('shadowing_complete_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trust_score', sa.Integer(), default=0),
        sa.Column('risk_score', sa.Integer(), default=50),
        sa.Column('status', sa.String(50), default='pending_verification'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_suspended', sa.Boolean(), default=False),
        sa.Column('status_notes', sa.Text(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('balance_usd', sa.Float(), default=0.0),
        sa.Column('balance_zig', sa.Float(), default=0.0),
        sa.Column('pending_usd', sa.Float(), default=0.0),
        sa.Column('pending_zig', sa.Float(), default=0.0),
        sa.Column('subscription_tier', sa.String(50), default='basic'),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ussd_pin_hash', sa.String(255), nullable=True),
        sa.Column('preferred_language', sa.String(10), default='en'),
        sa.Column('must_change_password', sa.Boolean(), default=False),
        sa.Column('notification_prefs', postgresql.JSONB(), nullable=True),
    )

    # Create farmer_profiles table
    op.create_table(
        'farmer_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('farm_name', sa.String(100), nullable=True),
        sa.Column('farm_size_hectares', sa.Float(), default=0.0),
        sa.Column('primary_crops', sa.String(255), nullable=True),
        sa.Column('production_scale', sa.String(20), default='SMALLHOLDER'),
    )

    # Create buyer_profiles table
    op.create_table(
        'buyer_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('company_name', sa.String(100), nullable=True),
        sa.Column('procurement_focus', sa.String(255), nullable=True),
        sa.Column('buyer_tier', sa.String(20), default='STANDARD'),
    )

    # Create agent_profiles table
    op.create_table(
        'agent_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('assigned_zone', sa.String(50), nullable=True),
        sa.Column('verification_count', sa.Integer(), default=0),
        sa.Column('agent_level', sa.Integer(), default=1),
    )

    # Create transporter_profiles table
    op.create_table(
        'transporter_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('vehicle_type', sa.String(50), nullable=True),
        sa.Column('carrying_capacity_kg', sa.Float(), default=0.0),
        sa.Column('operating_district', sa.String(50), nullable=True),
    )

    # Create trust_score_events table
    op.create_table(
        'trust_score_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('previous_score', sa.Integer(), nullable=False),
        sa.Column('new_score', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('trust_score_events')
    op.drop_table('transporter_profiles')
    op.drop_table('agent_profiles')
    op.drop_table('buyer_profiles')
    op.drop_table('farmer_profiles')
    op.drop_table('users')
