"""Loan schemas — spec §3.15 (functions 337-348)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan import LoanPurpose, LoanStatus


class LoanProductResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    purpose: LoanPurpose
    description: Optional[str] = None
    min_amount_usd: float
    max_amount_usd: float
    interest_rate_annual: float
    min_term_months: int
    max_term_months: int
    min_trust_score: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LoanProductCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=100)
    purpose: LoanPurpose
    description: Optional[str] = None
    min_amount_usd: float = Field(gt=0)
    max_amount_usd: float = Field(gt=0)
    interest_rate_annual: float = Field(ge=0, le=2)
    min_term_months: int = Field(ge=1, le=60)
    max_term_months: int = Field(ge=1, le=60)
    min_trust_score: int = Field(ge=0, le=100, default=60)


class LoanEligibilityResponse(BaseModel):
    eligible: bool
    max_amount_usd: float
    reasons: List[str]
    products: List[LoanProductResponse]


class LoanRepaymentCalcRequest(BaseModel):
    amount_usd: float = Field(gt=0)
    annual_rate: float = Field(ge=0, le=2)
    term_months: int = Field(ge=1, le=60)


class LoanRepaymentCalcResponse(BaseModel):
    amount_usd: float
    annual_rate: float
    term_months: int
    monthly_payment_usd: float
    total_repayment_usd: float
    total_interest_usd: float


class LoanApplyRequest(BaseModel):
    """F#338."""
    product_id: uuid.UUID
    amount_usd: float = Field(gt=0)
    term_months: int = Field(ge=1, le=60)
    purpose_text: Optional[str] = Field(default=None, max_length=2000)


class LoanRepaymentResponse(BaseModel):
    id: uuid.UUID
    amount_usd: float
    principal_component_usd: float
    interest_component_usd: float
    paid_at: datetime
    method: str
    reference: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    amount_usd: float
    term_months: int
    interest_rate_annual: float
    monthly_payment_usd: float
    purpose_text: Optional[str] = None
    status: LoanStatus
    agent_id: Optional[uuid.UUID] = None
    agent_verified_purpose: Optional[bool] = None
    agent_assessed_viable: Optional[bool] = None
    agent_notes: Optional[str] = None
    agent_reviewed_at: Optional[datetime] = None
    approver_id: Optional[uuid.UUID] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    next_due_date: Optional[datetime] = None
    total_repaid_usd: float
    outstanding_principal_usd: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanRepayRequest(BaseModel):
    amount_usd: float = Field(gt=0)


class LoanAgentVerifyRequest(BaseModel):
    """F#345, F#346 — agent submits purpose + viability assessment."""
    verified_purpose: bool
    assessed_viable: bool
    notes: Optional[str] = Field(default=None, max_length=2000)


class LoanApproveRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=2000)


class LoanRejectRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=2000)
