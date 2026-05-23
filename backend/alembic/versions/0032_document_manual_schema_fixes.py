"""Document manual schema fixes applied to synchronize ORM with database.

This migration documents all manual schema changes that were applied to fix
database schema drift issues. These changes were applied directly to the
database to resolve runtime errors and schema mismatches.

Changes documented:
1. Added driver_jobs table (was missing from database, exists in Driver model)
2. Added agent_training table (was missing from database, exists in Academy model)  
3. Added missing columns to drivers table to match Driver model:
   - vehicle_reg, vehicle_model, vehicle_year, vehicle_color
   - license_verified, current_district, insurance_verified, background_cleared
   - avg_rating, total_deliveries, successful_deliveries, warning_count
   - doc_national_id_front, doc_national_id_back, doc_license_front, doc_license_back
   - doc_vehicle_registration, doc_vehicle_photo, doc_profile_photo, doc_live_selfie
   - name, phone, updated_at
4. Added listing_id to orders table (exists in Order model)
5. Added sector to listings table (exists in Listing model)
6. Renamed transaction_type to type in transactions table (matches Transaction model)
7. Added updated_at to agents table (exists in Agent model)

Revision ID: 0032
Revises: 0031
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Create driver_jobs table
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS driver_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                distance_km DOUBLE PRECISION,
                total_transport_fee DOUBLE PRECISION,
                driver_payout DOUBLE PRECISION,
                buyer_rating INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                accepted_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                rejected_at TIMESTAMP WITH TIME ZONE
            )
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating driver_jobs table: {e}")
    
    # Create indexes for driver_jobs
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_driver_jobs_order_id ON driver_jobs(order_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_driver_jobs_driver_id ON driver_jobs(driver_id)"))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating driver_jobs indexes: {e}")
    
    # Create agent_training table
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_training (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID NOT NULL UNIQUE REFERENCES agents(id) ON DELETE CASCADE,
                module_1_status VARCHAR(20) DEFAULT 'not_started',
                module_2_status VARCHAR(20) DEFAULT 'not_started',
                module_3_status VARCHAR(20) DEFAULT 'not_started',
                module_4_status VARCHAR(20) DEFAULT 'not_started',
                module_5_status VARCHAR(20) DEFAULT 'not_started',
                module_6_status VARCHAR(20) DEFAULT 'not_started',
                module_7_status VARCHAR(20) DEFAULT 'not_started',
                module_8_status VARCHAR(20) DEFAULT 'not_started',
                module_9_status VARCHAR(20) DEFAULT 'not_started',
                module_10_status VARCHAR(20) DEFAULT 'not_started',
                module_1_score DOUBLE PRECISION,
                module_2_score DOUBLE PRECISION,
                module_3_score DOUBLE PRECISION,
                module_4_score DOUBLE PRECISION,
                module_5_score DOUBLE PRECISION,
                module_6_score DOUBLE PRECISION,
                module_7_score DOUBLE PRECISION,
                module_8_score DOUBLE PRECISION,
                module_9_score DOUBLE PRECISION,
                module_10_score DOUBLE PRECISION,
                final_exam_score DOUBLE PRECISION,
                certification_level VARCHAR(20) DEFAULT 'trainee',
                certified_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating agent_training table: {e}")
    
    # Create indexes for agent_training
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_training_agent_id ON agent_training(agent_id)"))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating agent_training indexes: {e}")
    
    # Add missing columns to drivers table
    columns_to_add = [
        ("vehicle_reg", "VARCHAR(50)"),
        ("vehicle_model", "VARCHAR(100)"),
        ("vehicle_year", "VARCHAR(10)"),
        ("vehicle_color", "VARCHAR(50)"),
        ("license_verified", "BOOLEAN DEFAULT FALSE"),
        ("current_district", "VARCHAR(100)"),
        ("insurance_verified", "BOOLEAN DEFAULT FALSE"),
        ("background_cleared", "BOOLEAN DEFAULT FALSE"),
        ("avg_rating", "DOUBLE PRECISION DEFAULT 0.0"),
        ("total_deliveries", "INTEGER DEFAULT 0"),
        ("successful_deliveries", "INTEGER DEFAULT 0"),
        ("warning_count", "INTEGER DEFAULT 0"),
        ("doc_national_id_front", "VARCHAR(500)"),
        ("doc_national_id_back", "VARCHAR(500)"),
        ("doc_license_front", "VARCHAR(500)"),
        ("doc_license_back", "VARCHAR(500)"),
        ("doc_vehicle_registration", "VARCHAR(500)"),
        ("doc_vehicle_photo", "VARCHAR(500)"),
        ("doc_profile_photo", "VARCHAR(500)"),
        ("doc_live_selfie", "VARCHAR(500)"),
        ("name", "VARCHAR(255)"),
        ("phone", "VARCHAR(20)"),
        ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
    ]
    
    for col_name, col_def in columns_to_add:
        try:
            conn.execute(text(f"ALTER TABLE drivers ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error adding column {col_name}: {e}")
    
    # Migrate data from legacy columns to new columns where applicable
    try:
        conn.execute(text("""
            UPDATE drivers 
            SET vehicle_reg = vehicle_plate 
            WHERE vehicle_reg IS NULL AND vehicle_plate IS NOT NULL
        """))
        conn.commit()
        
        conn.execute(text("""
            UPDATE drivers 
            SET current_district = operating_district 
            WHERE current_district IS NULL AND operating_district IS NOT NULL
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error migrating data: {e}")
    
    # Add listing_id to orders table
    try:
        conn.execute(text("""
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS listing_id UUID REFERENCES listings(id)
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error adding listing_id to orders: {e}")
    
    # Add sector to listings table
    try:
        conn.execute(text("""
            ALTER TABLE listings ADD COLUMN IF NOT EXISTS sector VARCHAR(50) NOT NULL DEFAULT 'CROPS'
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error adding sector to listings: {e}")
    
    # Rename transaction_type to type in transactions table (if it exists)
    try:
        # Check if transaction_type column exists and type column doesn't exist
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'transactions' AND column_name = 'transaction_type'
        """))
        if result.fetchone():
            conn.execute(text("""
                ALTER TABLE transactions RENAME COLUMN transaction_type TO type
            """))
            conn.commit()
    except Exception as e:
        # Column might already be renamed, ignore error
        print(f"Skipping transaction_type rename (may already be done): {e}")
        conn.rollback()
    
    # Add updated_at to agents table
    try:
        conn.execute(text("""
            ALTER TABLE agents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error adding updated_at to agents: {e}")


def downgrade() -> None:
    # Drop driver_jobs table
    try:
        op.execute("DROP TABLE IF EXISTS driver_jobs CASCADE")
    except Exception:
        pass
    
    # Drop agent_training table
    try:
        op.execute("DROP TABLE IF EXISTS agent_training CASCADE")
    except Exception:
        pass
    
    # Drop added columns from drivers table
    columns_to_drop = [
        "vehicle_reg", "vehicle_model", "vehicle_year", "vehicle_color",
        "license_verified", "current_district", "insurance_verified",
        "background_cleared", "avg_rating", "total_deliveries",
        "successful_deliveries", "warning_count", "doc_national_id_front",
        "doc_national_id_back", "doc_license_front", "doc_license_back",
        "doc_vehicle_registration", "doc_vehicle_photo", "doc_profile_photo",
        "doc_live_selfie", "name", "phone", "updated_at"
    ]
    
    for col_name in columns_to_drop:
        try:
            op.execute(f"ALTER TABLE drivers DROP COLUMN IF EXISTS {col_name}")
        except Exception:
            pass
    
    # Drop listing_id from orders table
    try:
        op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS listing_id")
    except Exception:
        pass
    
    # Drop sector from listings table
    try:
        op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS sector")
    except Exception:
        pass
    
    # Rename type back to transaction_type in transactions table
    try:
        op.execute("ALTER TABLE transactions RENAME COLUMN type TO transaction_type")
    except Exception:
        pass
    
    # Drop updated_at from agents table
    try:
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS updated_at")
    except Exception:
        pass
