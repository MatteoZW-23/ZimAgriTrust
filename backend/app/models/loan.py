"""Loan models — implements spec §3.15 (functions 337-348).

Loan products + applications + repayments + agent verification + admin
approval lifecycle. Funds disburse to the user's existing wallet on
approval; repayments deduct from wallet.
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
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LoanPurpose(str, enum.Enum):
    """Spec F#339 — loan products."""

    INPUT = "INPUT"            # seeds, fertilizer
    EQUIPMENT = "EQUIPMENT"    # machinery
    EXPANSION = "EXPANSION"    # acreage / scale-up
    EMERGENCY = "EMERGENCY"    # short-term cashflow


class LoanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AGENT_VERIFICATION = "AGENT_VERIFICATION"  # F#345, F#346
    APPROVED = "APPROVED"                       # F#347
    REJECTED = "REJECTED"                       # F#348
    DISBURSED = "DISBURSED"                     # F#344
    ACTIVE = "ACTIVE"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"


class LoanProduct(Base):
    """A loan product offering (seed, equipment, etc.). Configured by admin."""

    __tablename__ = "loan_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    purpose: Mapped[LoanPurpose] = mapped_column(Enum(LoanPurpose), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    min_amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    max_amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate_annual: Mapped[float] = mapped_column(Float, nullable=False)  # e.g. 0.18 for 18%
    min_term_months: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_term_months: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    min_trust_score: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Loan(Base):
    """A loan application/instance for a single user."""

    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loan_products.id"), nullable=False, index=True)

    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_rate_annual: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_payment_usd: Mapped[float] = mapped_column(Float, nullable=False)
    purpose_text: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.DRAFT, nullable=False)

    # Agent verification (F#345, F#346)
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    agent_verified_purpose: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agent_assessed_viable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    agent_notes: Mapped[Optional[str]] = mapped_column(Text)
    agent_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Admin approval (F#347, F#348)
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Disbursement (F#344)
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Running totals
    total_repaid_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    outstanding_principal_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product = relationship("LoanProduct")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanRepayment(Base):
    """A single repayment installment (F#342)."""

    __tablename__ = "loan_repayments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    principal_component_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    interest_component_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    method: Mapped[str] = mapped_column(String(40), default="WALLET", nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100))

    loan = relationship("Loan", back_populates="repayments")
