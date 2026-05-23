"""Add remaining missing columns to agents table and fix system_configs.group.

Revision ID: 0029
Revises: 0028
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add province column to agents table if it doesn't exist
    try:
        conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS province VARCHAR(50)"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Column might already exist
    
    # Add district column to agents table if it doesn't exist
    try:
        conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS district VARCHAR(50)"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass  # Column might already exist
    
    # Ensure system_configs.group column exists (in case 0028 failed)
    try:
        # Check if column exists
        column_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'system_configs' 
                AND column_name = 'group'
            )
        """)).scalar()
        
        if not column_exists:
            # Create the enum type if it doesn't exist
            try:
                conn.execute(text("CREATE TYPE configgroup AS ENUM ('general', 'finance', 'risk', 'features', 'region')"))
                conn.commit()
            except Exception:
                conn.rollback()
                pass  # Type might already exist
            
            # Add the column - "group" is a reserved keyword, need to quote it
            conn.execute(text('ALTER TABLE system_configs ADD COLUMN "group" configgroup DEFAULT \'general\''))
            conn.commit()
    except Exception:
        conn.rollback()
        pass


def downgrade() -> None:
    # Drop province and district columns from agents
    try:
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS province")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS district")
    except Exception:
        pass
    
    # Drop group column from system_configs
    try:
        op.execute("ALTER TABLE system_configs DROP COLUMN IF EXISTS group")
    except Exception:
        pass
