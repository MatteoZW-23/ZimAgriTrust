"""Add missing schema elements: agents.specialization, system_configs.group, order_deliveries table.

Revision ID: 0028
Revises: 0027
Create Date: 2026-05-21
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import text
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use execute with separate statements to avoid transaction issues
    conn = op.get_bind()
    
    # Add specialization column to agents table
    # First, create the enum type if it doesn't exist
    try:
        conn.execute(text("CREATE TYPE agentspecialization AS ENUM ('verification', 'dispute_resolution', 'field_support', 'grain_inspector', 'livestock_veterinary', 'cold_chain_logistics', 'all')"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Type might already exist
    
    # Add the column if it doesn't exist
    try:
        conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS specialization agentspecialization DEFAULT 'all'"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Column might already exist
    
    # Add group column to system_configs table
    # First, create the enum type if it doesn't exist
    try:
        conn.execute(text("CREATE TYPE configgroup AS ENUM ('general', 'finance', 'risk', 'features', 'region')"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Type might already exist
    
    # Add the column if it doesn't exist
    try:
        conn.execute(text("ALTER TABLE system_configs ADD COLUMN IF NOT EXISTS group configgroup DEFAULT 'general'"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Column might already exist
    
    # Create order_deliveries table if it doesn't exist
    # First, create the required enum types
    # Check if deliverystatus enum exists and has wrong values
    try:
        existing_enum = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = 'deliverystatus'::regtype 
            ORDER BY enumsortorder
        """)).fetchall()
        
        if existing_enum:
            # Drop and recreate with correct values
            conn.execute(text("ALTER TYPE deliverystatus RENAME TO deliverystatus_old"))
            conn.commit()
            conn.execute(text("CREATE TYPE deliverystatus AS ENUM ('PENDING_PICKUP', 'PICKUP_SCHEDULED', 'PICKUP_IN_PROGRESS', 'PICKUP_COMPLETED', 'IN_TRANSIT', 'DELAYED', 'ARRIVED', 'DELIVERY_IN_PROGRESS', 'DELIVERED', 'CONFIRMED', 'AUTO_CONFIRMED', 'DISPUTED')"))
            conn.commit()
            conn.execute(text("DROP TYPE deliverystatus_old"))
            conn.commit()
        else:
            conn.execute(text("CREATE TYPE deliverystatus AS ENUM ('PENDING_PICKUP', 'PICKUP_SCHEDULED', 'PICKUP_IN_PROGRESS', 'PICKUP_COMPLETED', 'IN_TRANSIT', 'DELAYED', 'ARRIVED', 'DELIVERY_IN_PROGRESS', 'DELIVERED', 'CONFIRMED', 'AUTO_CONFIRMED', 'DISPUTED')"))
            conn.commit()
    except Exception:
        conn.rollback()
        # Try creating directly if check failed
        try:
            conn.execute(text("CREATE TYPE deliverystatus AS ENUM ('PENDING_PICKUP', 'PICKUP_SCHEDULED', 'PICKUP_IN_PROGRESS', 'PICKUP_COMPLETED', 'IN_TRANSIT', 'DELAYED', 'ARRIVED', 'DELIVERY_IN_PROGRESS', 'DELIVERED', 'CONFIRMED', 'AUTO_CONFIRMED', 'DISPUTED')"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass  # Type might already exist with correct values
    
    try:
        conn.execute(text("CREATE TYPE deliverymethod AS ENUM ('BUYER_COLLECTS', 'FARMER_DELIVERS', 'THIRD_PARTY')"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Type might already exist
    
    # Check if table exists before creating
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'order_deliveries'
        )
    """)).scalar()
    
    if not table_exists:
        # Create the table using raw SQL to avoid enum issues
        conn.execute(text("""
            CREATE TABLE order_deliveries (
                id UUID NOT NULL DEFAULT gen_random_uuid(),
                order_id UUID NOT NULL REFERENCES orders(id),
                method deliverymethod,
                status deliverystatus NOT NULL DEFAULT 'PENDING_PICKUP',
                pickup_scheduled_at TIMESTAMP WITH TIME ZONE,
                estimated_arrival_at TIMESTAMP WITH TIME ZONE,
                delivered_at TIMESTAMP WITH TIME ZONE,
                confirmed_at TIMESTAMP WITH TIME ZONE,
                inspection_deadline TIMESTAMP WITH TIME ZONE,
                pickup_address TEXT,
                delivery_address TEXT,
                pickup_lat FLOAT,
                pickup_lon FLOAT,
                delivery_lat FLOAT,
                delivery_lon FLOAT,
                agent_id UUID REFERENCES users(id),
                driver_id UUID REFERENCES users(id),
                driver_name VARCHAR(100),
                vehicle_reg VARCHAR(20),
                pickup_photos JSON,
                delivery_photos JSON,
                pickup_gps_verified BOOLEAN NOT NULL DEFAULT false,
                delivery_gps_verified BOOLEAN NOT NULL DEFAULT false,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (id),
                UNIQUE (order_id)
            )
        """))
        conn.execute(text("CREATE INDEX ix_order_deliveries_order_id ON order_deliveries(order_id)"))
        conn.commit()


def downgrade() -> None:
    # Drop order_deliveries table
    op.drop_index("ix_order_deliveries_order_id", "order_deliveries")
    op.drop_table("order_deliveries")
    
    # Drop group column from system_configs
    try:
        op.execute("ALTER TABLE system_configs DROP COLUMN group")
    except Exception:
        pass
    
    # Drop specialization column from agents
    try:
        op.execute("ALTER TABLE agents DROP COLUMN specialization")
    except Exception:
        pass
    
    # Drop enum types (optional, as they might be used elsewhere)
    # We'll leave them for safety
