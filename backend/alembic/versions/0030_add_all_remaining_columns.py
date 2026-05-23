"""Add all remaining missing columns to agents and system_configs tables.

Revision ID: 0030
Revises: 0029
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add remaining agent columns
    agent_columns = [
        ("rating", "FLOAT DEFAULT 5.0"),
        ("current_load", "INTEGER DEFAULT 0"),
        ("is_available", "BOOLEAN DEFAULT TRUE"),
        ("avg_response_time", "FLOAT DEFAULT 24.0"),
        ("wallet_balance", "FLOAT DEFAULT 0.0"),
        ("pending_earnings", "FLOAT DEFAULT 0.0"),
    ]
    
    for col_name, col_def in agent_columns:
        try:
            conn.execute(text(f"ALTER TABLE agents ADD COLUMN IF NOT EXISTS {col_name} {col_def}"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass  # Column might already exist
    
    # Add remaining system_configs columns
    try:
        conn.execute(text("ALTER TABLE system_configs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    try:
        conn.execute(text("ALTER TABLE system_configs ADD COLUMN IF NOT EXISTS config_type VARCHAR(20) DEFAULT 'string'"))
        conn.commit()
    except Exception:
        conn.rollback()
        pass


def downgrade() -> None:
    # Drop agent columns
    for col_name in ["rating", "current_load", "is_available", "avg_response_time", "wallet_balance", "pending_earnings"]:
        try:
            op.execute(f"ALTER TABLE agents DROP COLUMN IF EXISTS {col_name}")
        except Exception:
            pass
    
    # Drop system_configs columns
    try:
        op.execute("ALTER TABLE system_configs DROP COLUMN IF EXISTS is_active")
    except Exception:
        pass
    
    try:
        op.execute("ALTER TABLE system_configs DROP COLUMN IF EXISTS config_type")
    except Exception:
        pass
