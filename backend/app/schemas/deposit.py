"""Pydantic schemas for the buyer deposit subsystem."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Payment methods ----------

class PaymentMethodCreate(BaseModel):
    channel: str = Field(pattern="^(ecocash|onemoney|innbucks|omari|bank_transfer|cash_agent)$")
    label: str
    last4: Optional[str] = None
    token: Optional[str] = None
    extra: Optional[dict[str, Any]] = None
    is_default: bool = False


class PaymentMethodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    channel: str
    label: str
    last4: Optional[str]
    is_default: bool
    is_verified: bool
    created_at: datetime


# ---------- Deposit intents ----------

class MobileMoneyDepositIn(BaseModel):
    channel: str = Field(pattern="^(ecocash|onemoney|innbucks|omari)$")
    amount: float = Field(gt=0)
    msisdn: str
    payment_method_id: Optional[UUID] = None


class BankDepositIn(BaseModel):
    amount: float = Field(gt=0)
    payment_method_id: Optional[UUID] = None


class CashAgentDepositIn(BaseModel):
    amount: float = Field(gt=0)
    agent_id: Optional[UUID] = None


class DepositIntentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    channel: str
    amount: float
    currency: str
    status: str
    external_reference: Optional[str]
    refundable_until: Optional[datetime]
    requires_id_verification: bool
    receipt_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class DepositConfirmIn(BaseModel):
    external_reference: str


class AgentCollectIn(BaseModel):
    receipt_no: str


# ---------- Auto top-up + recurring ----------

class AutoDepositRuleIn(BaseModel):
    payment_method_id: UUID
    threshold_usd: float = Field(gt=0)
    topup_amount_usd: float = Field(gt=0)


class AutoDepositRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    payment_method_id: UUID
    threshold_usd: float
    topup_amount_usd: float
    daily_max_topups: int
    is_active: bool
    last_triggered_at: Optional[datetime]


class RecurringDepositIn(BaseModel):
    payment_method_id: UUID
    amount_usd: float = Field(gt=0)
    cadence: str = Field(pattern="^(weekly|biweekly|monthly)$")
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    day_of_month: Optional[int] = Field(default=None, ge=1, le=28)


class RecurringDepositOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    payment_method_id: UUID
    amount_usd: float
    cadence: str
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    is_active: bool
    next_run_at: datetime
    last_run_at: Optional[datetime]


# ---------- Refund ----------

class RefundRequestIn(BaseModel):
    intent_id: UUID
    reason: Optional[str] = None


class RefundDecisionIn(BaseModel):
    approve: bool
    notes: Optional[str] = None


class RefundRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    deposit_intent_id: UUID
    amount: float
    fee: float
    net_refund: float
    reason: Optional[str]
    status: str
    created_at: datetime
    decided_at: Optional[datetime]
    processed_at: Optional[datetime]


# ---------- Limits ----------

class DepositLimitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_tier: str
    daily_limit: float
    weekly_limit: float
    monthly_limit: float
    per_transaction_limit: float
    id_verification_required_above: float
