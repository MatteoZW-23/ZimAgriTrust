"""Add order_number column to orders table.

The Order model expects an order_number column (unique, String(20), not null)
but it's missing from the database schema. This migration adds the column
and generates unique order numbers for existing orders.

Revision ID: 0039
Revises: 0038
Create Date: 2026-05-24
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Check if order_number column already exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'orders' AND column_name = 'order_number'
    """))
    if result.fetchone():
        print("order_number column already exists, skipping...")
        return
    
    # Add order_number column
    try:
        conn.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN order_number VARCHAR(20) UNIQUE
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error adding order_number column: {e}")
    
    # Generate unique order numbers for existing orders
    try:
        # Use a sequence to generate order numbers like ORD-00001, ORD-00002, etc.
        conn.execute(text("""
            CREATE SEQUENCE IF NOT EXISTS order_number_seq
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating sequence: {e}")
    
    try:
        # Update existing orders with generated order numbers
        conn.execute(text("""
            UPDATE orders 
            SET order_number = 'ORD-' || LPAD(nextval('order_number_seq')::text, 5, '0')
            WHERE order_number IS NULL
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating existing orders: {e}")
    
    # Make the column not null after all rows have values
    try:
        conn.execute(text("""
            ALTER TABLE orders 
            ALTER COLUMN order_number SET NOT NULL
        """))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error setting order_number to not null: {e}")


def downgrade() -> None:
    conn = op.get_bind()
    
    # Drop the column
    try:
        conn.execute(text("ALTER TABLE orders DROP COLUMN order_number"))
        conn.commit()
    except Exception:
        conn.rollback()
    
    # Drop the sequence
    try:
        conn.execute(text("DROP SEQUENCE IF EXISTS order_number_seq"))
        conn.commit()
    except Exception:
        conn.rollback()
