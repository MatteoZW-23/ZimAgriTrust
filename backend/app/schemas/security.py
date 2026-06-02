"""Pydantic schemas for the cash-security subsystem."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Super Admin auth ----------

class SuperAdminLoginRequest(BaseModel):
    username: str
    password: str


class SuperAdminPreMfaResponse(BaseModel):
    status: str
    pre_mfa_token: str
    expires_in: int
    mfa_methods: list[str]


class SuperAdminMfaVerifyRequest(BaseModel):
    pre_mfa_token: str
    mfa_code: str
    method: str = Field(default="totp", pattern="^(totp|yubikey)$")


class SuperAdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    super_admin: dict[str, Any]


class SuperAdminCreateRequest(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=12)
    phone_number: Optional[str] = None
    hardware_mfa_secret: Optional[str] = None
    yubikey_public_id: Optional[str] = None
    ip_whitelist: list[str] = Field(default_factory=list)
    approver_username: str
    approver_password: str
    approver_mfa_code: str
    approver_method: str = Field(default="totp", pattern="^(totp|yubikey)$")
    reason: str = Field(min_length=12, max_length=500)
    is_root: bool = False


# ---------- Admin approvals ----------

class ApprovalRequestIn(BaseModel):
    resource_type: str
    resource_id: str
    action: str
    amount: float
    currency: str = "USD"
    reason: Optional[str] = None


class ApprovalDecisionIn(BaseModel):
    reason: Optional[str] = None


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    resource_type: str
    resource_id: str
    action: str
    amount: float
    currency: str
    status: str
    reason: Optional[str] = None
    requested_by: UUID
    requested_at: datetime
    approved_by_1: Optional[UUID] = None
    approved_at_1: Optional[datetime] = None
    approved_by_2: Optional[UUID] = None
    approved_at_2: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    fully_approved_at: Optional[datetime] = None


# ---------- Fraud alerts ----------

class FraudAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: Optional[UUID]
    alert_type: str
    severity: str
    details: Optional[dict[str, Any]] = None
    related_resource_type: Optional[str] = None
    related_resource_id: Optional[str] = None
    resolved: bool
    created_at: datetime


class FraudAlertResolveIn(BaseModel):
    notes: Optional[str] = None


# ---------- Withdrawal limits ----------

class WithdrawalLimitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_tier: str
    daily_limit: float
    weekly_limit: float
    monthly_limit: float
    per_transaction_limit: float
    min_trust_score: Optional[int] = None


class WithdrawalLimitUpdateIn(BaseModel):
    daily_limit: float = Field(ge=0)
    weekly_limit: float = Field(ge=0)
    monthly_limit: float = Field(ge=0)
    per_transaction_limit: float = Field(ge=0)
    min_trust_score: Optional[int] = Field(default=None, ge=0, le=100)
    mfa_code: str = Field(min_length=6, max_length=48)
    mfa_method: str = Field(default="totp", pattern="^(totp|yubikey)$")


# ---------- Audit ----------

class AuditChainStatus(BaseModel):
    ok: bool
    checked: int
    first_break_id: Optional[int] = None
    details: list[dict[str, Any]] = Field(default_factory=list)


# ---------- Two-key escrow ----------

class EscrowReleaseRequestIn(BaseModel):
    order_id: UUID
    mfa_code: str = Field(min_length=6, max_length=48)
    mfa_method: str = Field(default="totp", pattern="^(totp|yubikey)$")


class EscrowReleaseConfirmIn(BaseModel):
    order_id: UUID
    otp: str
    handover_code: Optional[str] = None
    mfa_code: str = Field(min_length=6, max_length=48)
    mfa_method: str = Field(default="totp", pattern="^(totp|yubikey)$")


# ---------- Emergency ----------

class EmergencyShutdownIn(BaseModel):
    reason: str
    confirm: bool = False
    mfa_code: str = Field(min_length=6, max_length=48)
    mfa_method: str = Field(default="totp", pattern="^(totp|yubikey)$")
