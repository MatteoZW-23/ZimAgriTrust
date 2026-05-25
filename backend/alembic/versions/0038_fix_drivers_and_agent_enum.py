"""Fix missing driver column and agent specialization enum case.

Adds vehicle_capacity_kg column to drivers table and updates the 
AgentSpecialization enum to use uppercase values to match the model.

Changes:
1. Add vehicle_capacity_kg column to drivers table (default 1000.0)
2. Drop and recreate AgentSpecialization enum with uppercase values
3. Update existing agent records to use uppercase enum values

Revision ID: 0038
Revises: 0037
Create Date: 2026-05-24
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # ------------------------------------------------------------------
    # 1. Add missing vehicle_capacity_kg column to drivers table
    # ------------------------------------------------------------------
    try:
        conn.execute(text("""
            ALTER TABLE drivers 
            ADD COLUMN IF NOT EXISTS vehicle_capacity_kg FLOAT DEFAULT 1000.0
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error adding vehicle_capacity_kg: {e}")
    
    # ------------------------------------------------------------------
    # 2. Fix AgentSpecialization enum - change to uppercase values
    # ------------------------------------------------------------------
    
    # Add new uppercase values to the existing enum
    new_values = [
        'VERIFICATION', 'DISPUTE_RESOLUTION', 'FIELD_SUPPORT',
        'GRAIN_INSPECTOR', 'LIVESTOCK_VETERINARY', 'COLD_CHAIN_LOGISTICS',
        'FISHERY_QUALITY', 'MANAGEMENT', 'ALL'
    ]
    
    for val in new_values:
        try:
            conn.execute(text(f"ALTER TYPE agentspecialization ADD VALUE IF NOT EXISTS '{val}'"))
            conn.commit()
        except Exception as e:
            conn.rollback()
            # Value might already exist, continue
    
    # Update existing records to use uppercase values (only if they are lowercase)
    try:
        # Check if any lowercase values exist before updating (cast to text to avoid enum errors)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM agents WHERE specialization::text IN ('all', 'verification', 'dispute_resolution', 'field_support', 'grain_inspector', 'livestock_veterinary', 'cold_chain_logistics')
        """))
        lowercase_count = result.scalar()
        
        if lowercase_count > 0:
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'ALL' WHERE specialization::text = 'all'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'VERIFICATION' WHERE specialization::text = 'verification'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'DISPUTE_RESOLUTION' WHERE specialization::text = 'dispute_resolution'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'FIELD_SUPPORT' WHERE specialization::text = 'field_support'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'GRAIN_INSPECTOR' WHERE specialization::text = 'grain_inspector'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'LIVESTOCK_VETERINARY' WHERE specialization::text = 'livestock_veterinary'
            """))
            conn.execute(text("""
                UPDATE agents 
                SET specialization = 'COLD_CHAIN_LOGISTICS' WHERE specialization::text = 'cold_chain_logistics'
            """))
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating agent specialization values: {e}")
    
    # Remove old lowercase values by recreating the enum
    # First, alter column to text type temporarily
    try:
        conn.execute(text("""
            ALTER TABLE agents 
            ALTER COLUMN specialization TYPE VARCHAR(50) 
            USING specialization::VARCHAR(50)
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error altering column to varchar: {e}")
    
    # Drop the default value on the column (it depends on the enum)
    try:
        conn.execute(text("""
            ALTER TABLE agents 
            ALTER COLUMN specialization DROP DEFAULT
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error dropping default: {e}")
    
    # Drop the old enum
    try:
        conn.execute(text("DROP TYPE IF EXISTS agentspecialization"))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error dropping old enum: {e}")
    
    # Create the new enum with uppercase values only
    try:
        conn.execute(text("""
            CREATE TYPE agentspecialization AS ENUM (
                'VERIFICATION',
                'DISPUTE_RESOLUTION', 
                'FIELD_SUPPORT',
                'GRAIN_INSPECTOR',
                'LIVESTOCK_VETERINARY',
                'COLD_CHAIN_LOGISTICS',
                'FISHERY_QUALITY',
                'MANAGEMENT',
                'ALL'
            )
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating new enum: {e}")
    
    # Alter the column back to use the new enum type
    try:
        conn.execute(text("""
            ALTER TABLE agents 
            ALTER COLUMN specialization TYPE agentspecialization 
            USING specialization::agentspecialization
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error altering column type back to enum: {e}")


def downgrade() -> None:
    conn = op.get_bind()
    
    # Drop vehicle_capacity_kg from drivers
    try:
        conn.execute(text("ALTER TABLE drivers DROP COLUMN IF EXISTS vehicle_capacity_kg"))
        conn.commit()
    except Exception:
        conn.rollback()
    
    # Revert AgentSpecialization enum to lowercase
    try:
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'all' WHERE specialization = 'ALL'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'verification' WHERE specialization = 'VERIFICATION'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'dispute_resolution' WHERE specialization = 'DISPUTE_RESOLUTION'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'field_support' WHERE specialization = 'FIELD_SUPPORT'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'grain_inspector' WHERE specialization = 'GRAIN_INSPECTOR'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'livestock_veterinary' WHERE specialization = 'LIVESTOCK_VETERINARY'
        """))
        conn.execute(text("""
            UPDATE agents 
            SET specialization = 'cold_chain_logistics' WHERE specialization = 'COLD_CHAIN_LOGISTICS'
        """))
        conn.commit()
    except Exception:
        conn.rollback()
    
    # Drop and recreate with lowercase values
    try:
        conn.execute(text("DROP TYPE IF EXISTS agentspecialization"))
        conn.commit()
    except Exception:
        conn.rollback()
    
    try:
        conn.execute(text("""
            CREATE TYPE agentspecialization AS ENUM (
                'verification',
                'dispute_resolution',
                'field_support', 
                'grain_inspector',
                'livestock_veterinary',
                'cold_chain_logistics',
                'all'
            )
        """))
        conn.commit()
    except Exception:
        conn.rollback()
    
    try:
        conn.execute(text("""
            ALTER TABLE agents 
            ALTER COLUMN specialization TYPE agentspecialization 
            USING specialization::agentspecialization
        """))
        conn.commit()
    except Exception:
        conn.rollback()
