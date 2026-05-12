"""
Buyer deposit subsystem — pre-funding the wallet from external sources.

Tables:
- payment_methods         : tokenised links to a buyer's preferred channels
- deposit_intents         : every deposit attempt (pending → completed/failed)
- auto_deposit_rules      : top-up when balance falls below threshold
- recurring_deposit_rules : weekly / monthly scheduled deposits
- deposit_refund_requests : refund of unused deposit within 7-day window
- deposit_limits          : per-tier daily/weekly caps (override-able)

The actual fund movement uses the existing `Transaction` table with type=DEPOSIT.
A deposit_intent is created first; on confirmation the transaction is created
and the intent is marked completed.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DepositChannel(str, enum.Enum):
    ECOCASH = "ecocash"
    ONEMONEY = "onemoney"
    BANK_TRANSFER = "bank_transfer"
    CASH_AGENT = "cash_agent"  # agent-assisted in-person deposit


class DepositIntentStatus(str, enum.Enum):
    PENDING = "pending"          # awaiting external confirmation
    AGENT_HELD = "agent_held"    # cash collected by agent, awaiting reconciliation
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUND_REQUESTED = "refund_requested"
    REFUNDED = "refunded"


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"


class RecurrenceCadence(str, enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PaymentMethod(Base):
    """A linked deposit channel for a user (tokenised — never store full PAN/MSISDN)."""
    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[DepositChannel] = mapped_column(Enum(DepositChannel), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)  # "EcoCash personal", "CABS savings"
    last4: Mapped[Optional[str]] = mapped_column(String(8))           # masked display
    token: Mapped[Optional[str]] = mapped_column(String(255))         # provider token / reference
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    extra: Mapped[Optional[dict]] = mapped_column(JSON)               # bank_name, account_holder
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DepositIntent(Base):
    """A specific deposit attempt — the source of truth for reconciliation."""
    __tablename__ = "deposit_intents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[DepositChannel] = mapped_column(Enum(DepositChannel), nullable=False, index=True)
    payment_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("payment_methods.id"))

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")

    status: Mapped[DepositIntentStatus] = mapped_column(
        Enum(DepositIntentStatus), default=DepositIntentStatus.PENDING, index=True
    )
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Resulting transaction (once completed)
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("transactions.id"))

    # Cash-via-agent specific
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    agent_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    agent_reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    agent_receipt_no: Mapped[Optional[str]] = mapped_column(String(64))

    # Bank-transfer specific
    bank_reference: Mapped[Optional[str]] = mapped_column(String(64))

    # Receipt
    receipt_url: Mapped[Optional[str]] = mapped_column(String(255))

    # If this intent is unused & refundable: when does the 7-day window close?
    refundable_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Used for ID-verification gate on large deposits
    requires_id_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verification_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AutoDepositRule(Base):
    """Auto-top-up: if balance < threshold, deposit a fixed amount."""
    __tablename__ = "auto_deposit_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    payment_method_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_methods.id"), nullable=False)

    threshold_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # trigger when below
    topup_amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    daily_max_topups: Mapped[int] = mapped_column(Integer, default=2)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RecurringDepositSchedule(Base):
    """Weekly / monthly cron-like recurring deposit."""
    __tablename__ = "recurring_deposit_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    payment_method_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_methods.id"), nullable=False)

    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    cadence: Mapped[RecurrenceCadence] = mapped_column(Enum(RecurrenceCadence), nullable=False)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)       # 0=Mon..6=Sun
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer)      # 1..28

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DepositRefundRequest(Base):
    """Refund of an unused deposit within the 7-day refund window."""
    __tablename__ = "deposit_refund_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deposit_intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deposit_intents.id"), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net_refund: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[RefundStatus] = mapped_column(Enum(RefundStatus), default=RefundStatus.PENDING, index=True)
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    decision_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DepositLimit(Base):
    """Per-tier daily / weekly deposit caps (super-admin overridable)."""
    __tablename__ = "deposit_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tier: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # mirror UserTier values

    daily_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    weekly_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    monthly_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    per_transaction_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    id_verification_required_above: Mapped[float] = mapped_column(Numeric(12, 2), default=1000.0)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_tier", name="uq_deposit_limit_tier"),)
