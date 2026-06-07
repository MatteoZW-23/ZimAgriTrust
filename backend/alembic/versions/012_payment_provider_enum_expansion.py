from __future__ import annotations

from alembic import op


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE payoutmethodtype ADD VALUE IF NOT EXISTS 'INNBUCKS'")
    op.execute("ALTER TYPE payoutmethodtype ADD VALUE IF NOT EXISTS 'OMARI'")
    op.execute("ALTER TYPE payoutmethodtype ADD VALUE IF NOT EXISTS 'BANK_TRANSFER'")
    op.execute("ALTER TYPE payoutmethodprovider ADD VALUE IF NOT EXISTS 'INNBUCKS'")
    op.execute("ALTER TYPE payoutmethodprovider ADD VALUE IF NOT EXISTS 'OMARI'")
    op.execute("ALTER TYPE payoutmethodprovider ADD VALUE IF NOT EXISTS 'BANK_TRANSFER'")
    op.execute("ALTER TYPE depositchannel ADD VALUE IF NOT EXISTS 'innbucks'")
    op.execute("ALTER TYPE depositchannel ADD VALUE IF NOT EXISTS 'omari'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be dropped safely without recreating dependent columns.
    pass
