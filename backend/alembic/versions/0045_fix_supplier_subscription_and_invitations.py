"""Fix supplier_profiles subscription_plan column and invitations.created_by constraint.

This migration:
1. Adds missing subscription_plan column to supplier_profiles table
2. Makes invitations.created_by foreign key nullable to handle missing users

Revision ID: 0045
Revises: 0044
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ========================================================================
    # 1. Add missing subscription_plan column to supplier_profiles
    # ========================================================================
    result = conn.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'supplier_profiles' AND column_name = 'subscription_plan'"
    ))
    if not result.fetchone():
        conn.execute(text(
            "ALTER TABLE supplier_profiles ADD COLUMN subscription_plan VARCHAR(20)"
        ))

    # ========================================================================
    # 2. Make invitations.created_by nullable (if it's not already)
    # ========================================================================
    # First, drop the foreign key constraint if it exists
    try:
        conn.execute(text(
            "ALTER TABLE invitations DROP CONSTRAINT IF EXISTS invitations_created_by_fkey"
        ))
    except Exception:
        pass

    # Make the column nullable if it's not already
    result = conn.execute(text(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name = 'invitations' AND column_name = 'created_by'"
    ))
    row = result.fetchone()
    if row and row[0] == 'NO':
        conn.execute(text(
            "ALTER TABLE invitations ALTER COLUMN created_by DROP NOT NULL"
        ))

    # Re-add the foreign key constraint with nullable support
    conn.execute(text(
        "ALTER TABLE invitations "
        "ADD CONSTRAINT invitations_created_by_fkey "
        "FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL"
    ))


def downgrade() -> None:
    conn = op.get_bind()

    # Remove subscription_plan column
    try:
        conn.execute(text(
            "ALTER TABLE supplier_profiles DROP COLUMN IF EXISTS subscription_plan"
        ))
    except Exception:
        pass

    # Revert invitations.created_by to NOT NULL (optional, may fail if data exists)
    try:
        conn.execute(text(
            "ALTER TABLE invitations DROP CONSTRAINT IF EXISTS invitations_created_by_fkey"
        ))
        conn.execute(text(
            "ALTER TABLE invitations ALTER COLUMN created_by SET NOT NULL"
        ))
        conn.execute(text(
            "ALTER TABLE invitations "
            "ADD CONSTRAINT invitations_created_by_fkey "
            "FOREIGN KEY (created_by) REFERENCES users(id)"
        ))
    except Exception:
        pass
