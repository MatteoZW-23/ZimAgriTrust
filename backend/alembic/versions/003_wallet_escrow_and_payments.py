from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

TABLES = ['ledger_entries', 'ledger_reconciliations', 'escrow_accounts', 'escrow_transactions', 'payment_methods', 'deposit_intents', 'auto_deposit_rules', 'recurring_deposit_schedules', 'deposit_refund_requests', 'deposit_limits', 'user_payout_methods', 'withdrawal_limits', 'payment_allocations', 'settlements']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

