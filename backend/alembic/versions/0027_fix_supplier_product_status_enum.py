"""Fix supplier product status enum to include uppercase values.

Revision ID: 0027
Revises: 0026
Create Date: 2026-05-21
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter the enum to include uppercase values alongside lowercase
    # PostgreSQL doesn't support ALTER TYPE ... ADD VALUE IF NOT EXISTS directly
    # We need to drop and recreate the type, or use a workaround
    
    # First, drop the default value on the column
    op.execute("ALTER TABLE supplier_products ALTER COLUMN status DROP DEFAULT")
    
    # Rename the old type
    op.execute("ALTER TYPE supplierproductstatus RENAME TO supplierproductstatus_old")
    
    # Create the new type with both uppercase and lowercase values
    op.execute("CREATE TYPE supplierproductstatus AS ENUM ('ACTIVE', 'active', 'OUT_OF_STOCK', 'out_of_stock', 'DRAFT', 'draft', 'EXPIRED', 'expired', 'SUSPENDED', 'suspended')")
    
    # Update the column to use the new type
    op.execute("ALTER TABLE supplier_products ALTER COLUMN status TYPE supplierproductstatus USING status::text::supplierproductstatus")
    
    # Restore the default value
    op.execute("ALTER TABLE supplier_products ALTER COLUMN status SET DEFAULT 'draft'")
    
    # Drop the old type
    op.execute("DROP TYPE supplierproductstatus_old")


def downgrade() -> None:
    # Revert to lowercase-only values
    op.execute("ALTER TYPE supplierproductstatus RENAME TO supplierproductstatus_new")
    
    # Recreate the original type with lowercase values only
    op.execute("CREATE TYPE supplierproductstatus AS ENUM ('active', 'out_of_stock', 'draft', 'expired', 'suspended')")
    
    # Update the column to use the old type
    op.execute("ALTER TABLE supplier_products ALTER COLUMN status TYPE supplierproductstatus USING status::text::supplierproductstatus")
    
    # Drop the new type
    op.execute("DROP TYPE supplierproductstatus_new")
