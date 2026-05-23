"""add agent commission tracking

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade():
    # Add agent tracking fields to listings table
    op.add_column('listings', sa.Column('verified_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True))
    op.add_column('listings', sa.Column('verified_by_ai', sa.Boolean(), nullable=False, server_default='false'))

    # Drop old verified_by column (string) if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'listings' AND column_name = 'verified_by'
            ) THEN
                ALTER TABLE listings DROP COLUMN verified_by;
            END IF;
        END $$;
    """)

    # Add agent tracking fields to orders table
    op.add_column('orders', sa.Column('fulfilled_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True))
    op.add_column('orders', sa.Column('field_support_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True))

    # Add agent tracking field to disputes table
    op.add_column('disputes', sa.Column('resolved_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True))

    # Drop old agent_assigned column (was referencing users.id) if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'disputes' AND column_name = 'agent_assigned'
            ) THEN
                ALTER TABLE disputes DROP COLUMN agent_assigned;
            END IF;
        END $$;
    """)

    # Create indexes for faster lookups
    op.create_index('idx_listings_verified_by_agent', 'listings', ['verified_by_agent_id'])
    op.create_index('idx_orders_fulfilled_by_agent', 'orders', ['fulfilled_by_agent_id'])
    op.create_index('idx_orders_field_support_by_agent', 'orders', ['field_support_by_agent_id'])
    op.create_index('idx_disputes_resolved_by_agent', 'disputes', ['resolved_by_agent_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_disputes_resolved_by_agent', table_name='disputes')
    op.drop_index('idx_orders_field_support_by_agent', table_name='orders')
    op.drop_index('idx_orders_fulfilled_by_agent', table_name='orders')
    op.drop_index('idx_listings_verified_by_agent', table_name='listings')
    
    # Restore old agent_assigned column
    op.add_column('disputes', sa.Column('agent_assigned', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    
    # Drop new resolved_by_agent_id column
    op.drop_column('disputes', 'resolved_by_agent_id')
    
    # Drop new order columns
    op.drop_column('orders', 'field_support_by_agent_id')
    op.drop_column('orders', 'fulfilled_by_agent_id')
    
    # Restore old verified_by column
    op.add_column('listings', sa.Column('verified_by', sa.String(length=100), nullable=True))
    
    # Drop new listing columns
    op.drop_column('listings', 'verified_by_ai')
    op.drop_column('listings', 'verified_by_agent_id')
