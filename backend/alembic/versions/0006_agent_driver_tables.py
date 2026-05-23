"""Add agent and driver tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-20 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('agent_code', sa.String(20), unique=True, nullable=False),
        sa.Column('pin_hash', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), default='trainee'),
        sa.Column('assigned_zone', sa.String(50), nullable=True),
        sa.Column('commission_rate', sa.Float(), default=0.05),
        sa.Column('total_commission', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create agent_applications table
    op.create_table(
        'agent_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('national_id', sa.String(20), nullable=False),
        sa.Column('phone_number', sa.String(32), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('documents', postgresql.JSONB(), nullable=True),
        sa.Column('references', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
    )

    # Create drivers table
    op.create_table(
        'drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('vehicle_type', sa.String(50), nullable=False),
        sa.Column('vehicle_plate', sa.String(20), unique=True, nullable=False),
        sa.Column('carrying_capacity_kg', sa.Float(), nullable=False),
        sa.Column('operating_district', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('license_number', sa.String(50), nullable=True),
        sa.Column('license_expiry', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rejection_note', sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table('drivers')
    op.drop_table('agent_applications')
    op.drop_table('agents')
