"""add ledger system

Revision ID: 0017
Revises: 0016
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None

# Enums
LEDGER_ACCOUNT_TYPE_ENUM = postgresql.ENUM(
    'CASH_USD', 'CASH_ZIG', 'PENDING_ESCROW_USD', 'PENDING_ESCROW_ZIG', 'RECEIVABLES',
    'USER_BALANCE_USD', 'USER_BALANCE_ZIG', 'PAYABLES', 'PLATFORM_FEE_USD', 'PLATFORM_FEE_ZIG',
    'TRANSPORT_FEE_USD', 'INSURANCE_FEE_USD', 'PROVIDER_PAYOUT_USD', 'PROVIDER_PAYOUT_ZIG',
    'REFUND_USD', 'REFUND_ZIG',
    name='ledgeraccounttype',
    create_type=False,
)
LEDGER_ENTRY_TYPE_ENUM = postgresql.ENUM(
    'DEBIT', 'CREDIT',
    name='ledgerentrytype',
    create_type=False,
)


def upgrade():
    # Create enum types with raw SQL and try/except to handle duplicates
    try:
        op.get_bind().execute(text("CREATE TYPE ledgeraccounttype AS ENUM ('CASH_USD', 'CASH_ZIG', 'PENDING_ESCROW_USD', 'PENDING_ESCROW_ZIG', 'RECEIVABLES', 'USER_BALANCE_USD', 'USER_BALANCE_ZIG', 'PAYABLES', 'PLATFORM_FEE_USD', 'PLATFORM_FEE_ZIG', 'TRANSPORT_FEE_USD', 'INSURANCE_FEE_USD', 'PROVIDER_PAYOUT_USD', 'PROVIDER_PAYOUT_ZIG', 'REFUND_USD', 'REFUND_ZIG')"))
    except Exception:
        pass
    try:
        op.get_bind().execute(text("CREATE TYPE ledgerentrytype AS ENUM ('DEBIT', 'CREDIT')"))
    except Exception:
        pass
    # Create ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='RESTRICT'), nullable=True, index=True),
        sa.Column('account_type', LEDGER_ACCOUNT_TYPE_ENUM, nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True, index=True),
        sa.Column('entry_type', LEDGER_ENTRY_TYPE_ENUM, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=5), nullable=False, server_default='USD'),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True, unique=True, index=True),
    )
    
    # Create indexes
    op.create_index('idx_ledger_account_user', 'ledger_entries', ['account_type', 'user_id'])
    op.create_index('idx_ledger_transaction', 'ledger_entries', ['transaction_id'])
    op.create_index('idx_ledger_created_at', 'ledger_entries', ['created_at'])
    op.create_index('idx_ledger_idempotency', 'ledger_entries', ['idempotency_key'])
    
    # Create ledger_reconciliations table
    op.create_table(
        'ledger_reconciliations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('account_type', LEDGER_ACCOUNT_TYPE_ENUM, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('currency', sa.String(length=5), nullable=False, server_default='USD'),
        sa.Column('total_debits', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_credits', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('actual_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('difference', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_balanced', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('discrepancies', postgresql.JSON(), nullable=True),
        sa.Column('reconciled_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('reconciled_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_reconciliation_account', 'ledger_reconciliations', ['account_type', 'user_id'])
    op.create_index('idx_reconciliation_date', 'ledger_reconciliations', ['reconciled_at'])


def downgrade():
    # Drop ledger_reconciliations table
    op.drop_index('idx_reconciliation_date', table_name='ledger_reconciliations')
    op.drop_index('idx_reconciliation_account', table_name='ledger_reconciliations')
    op.drop_table('ledger_reconciliations')
    
    # Drop ledger_entries table
    op.drop_index('idx_ledger_idempotency', table_name='ledger_entries')
    op.drop_index('idx_ledger_created_at', table_name='ledger_entries')
    op.drop_index('idx_ledger_transaction', table_name='ledger_entries')
    op.drop_index('idx_ledger_account_user', table_name='ledger_entries')
    op.drop_table('ledger_entries')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS ledgerentrytype')
    op.execute('DROP TYPE IF EXISTS ledgeraccounttype')
