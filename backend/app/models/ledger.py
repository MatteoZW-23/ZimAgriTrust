"""
Double-Entry Ledger System for Financial Consistency

Every financial movement creates two entries:
- Debit: Money leaving an account
- Credit: Money entering an account

Total debits must always equal total credits (accounting equation).
This prevents data corruption and enables reconciliation.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, String, DateTime, Boolean, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LedgerEntryType(str, enum.Enum):
    """Types of ledger entries"""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class LedgerAccountType(str, enum.Enum):
    """Chart of accounts"""
    # Asset accounts
    CASH_USD = "CASH_USD"
    CASH_ZIG = "CASH_ZIG"
    PENDING_ESCROW_USD = "PENDING_ESCROW_USD"
    PENDING_ESCROW_ZIG = "PENDING_ESCROW_ZIG"
    RECEIVABLES = "RECEIVABLES"
    
    # Liability accounts
    USER_BALANCE_USD = "USER_BALANCE_USD"
    USER_BALANCE_ZIG = "USER_BALANCE_ZIG"
    PAYABLES = "PAYABLES"
    
    # Revenue accounts
    PLATFORM_FEE_USD = "PLATFORM_FEE_USD"
    PLATFORM_FEE_ZIG = "PLATFORM_FEE_ZIG"
    TRANSPORT_FEE_USD = "TRANSPORT_FEE_USD"
    INSURANCE_FEE_USD = "INSURANCE_FEE_USD"
    SUBSCRIPTION_REVENUE_USD = "SUBSCRIPTION_REVENUE_USD"
    SUBSCRIPTION_REVENUE_ZIG = "SUBSCRIPTION_REVENUE_ZIG"
    
    # Expense accounts
    PROVIDER_PAYOUT_USD = "PROVIDER_PAYOUT_USD"
    PROVIDER_PAYOUT_ZIG = "PROVIDER_PAYOUT_ZIG"
    REFUND_USD = "REFUND_USD"
    REFUND_ZIG = "REFUND_ZIG"
    WITHDRAWAL_PENDING_USD = "WITHDRAWAL_PENDING_USD"
    WITHDRAWAL_PENDING_ZIG = "WITHDRAWAL_PENDING_ZIG"


class LedgerEntry(Base):
    """
    Immutable double-entry ledger record.
    Never deleted. Never modified. Only appended.
    """
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to transaction for traceability
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id"), nullable=False, index=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)
    
    # Account identification
    account_type: Mapped[LedgerAccountType] = mapped_column(Enum(LedgerAccountType), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Entry details
    entry_type: Mapped[LedgerEntryType] = mapped_column(Enum(LedgerEntryType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD", nullable=False)
    
    # Running balance for this account (redundant for performance, validated by reconciliation)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Metadata
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entry_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON field for additional context
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Idempotency
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    
    # Relationships
    transaction = relationship("Transaction")
    
    __table_args__ = (
        Index('idx_ledger_account_user', 'account_type', 'user_id'),
        Index('idx_ledger_transaction', 'transaction_id'),
        Index('idx_ledger_created_at', 'created_at'),
        Index('idx_ledger_idempotency', 'idempotency_key'),
    )

    def __repr__(self):
        return f"<LedgerEntry {self.entry_type} {self.amount} {self.currency} {self.account_type}>"


class LedgerReconciliation(Base):
    """
    Periodic reconciliation reports to validate ledger integrity.
    Ensures total debits equal total credits and balances match.
    """
    __tablename__ = "ledger_reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reconciliation scope
    account_type: Mapped[Optional[LedgerAccountType]] = mapped_column(Enum(LedgerAccountType), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    
    # Reconciliation results
    total_debits: Mapped[float] = mapped_column(Float, default=0.0)
    total_credits: Mapped[float] = mapped_column(Float, default=0.0)
    expected_balance: Mapped[float] = mapped_column(Float, default=0.0)
    actual_balance: Mapped[float] = mapped_column(Float, default=0.0)
    difference: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status
    is_balanced: Mapped[bool] = mapped_column(Boolean, default=True)
    discrepancies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON field for discrepancy details
    
    # Audit
    reconciled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reconciled_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    __table_args__ = (
        Index('idx_reconciliation_account', 'account_type', 'user_id'),
        Index('idx_reconciliation_date', 'reconciled_at'),
    )
