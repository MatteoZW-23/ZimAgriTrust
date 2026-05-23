"""Add missing core columns to orders, transactions, and listings tables.

Revision ID: 0031
Revises: 0030
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add listing_id to orders table
    try:
        conn.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS listing_id UUID REFERENCES listings(id)
        """))
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    # Add type column to transactions table
    try:
        conn.execute(text("""
            ALTER TABLE transactions 
            ADD COLUMN IF NOT EXISTS type VARCHAR(20) NOT NULL DEFAULT 'PAYMENT'
        """))
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    # Add sector column to listings table
    try:
        conn.execute(text("""
            ALTER TABLE listings 
            ADD COLUMN IF NOT EXISTS sector VARCHAR(50) NOT NULL DEFAULT 'CROPS'
        """))
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    # Add updated_at to agents table
    try:
        conn.execute(text("""
            ALTER TABLE agents 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
        """))
        conn.commit()
    except Exception:
        conn.rollback()
        pass


def downgrade() -> None:
    # Drop listing_id from orders
    try:
        op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS listing_id")
    except Exception:
        pass
    
    # Drop type from transactions
    try:
        op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS type")
    except Exception:
        pass
    
    # Drop sector from listings
    try:
        op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS sector")
    except Exception:
        pass
    
    # Drop updated_at from agents
    try:
        op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS updated_at")
    except Exception:
        pass
