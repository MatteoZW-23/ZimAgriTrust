from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from app.models.fintech.wallet import WalletType, Currency
from app.models.fintech.payment import PaymentProvider, PaymentStatus
from app.models.fintech.subscription import SubscriptionPlan, SubscriptionStatus


# Wallet schemas
class WalletResponse(BaseModel):
    wallet_id: str
    type: str
    currency: str
    balance_minor: int
    pending_minor: int
    available_minor: int


class TransferRequest(BaseModel):
    from_wallet_id: uuid.UUID
    to_wallet_id: uuid.UUID
    amount_minor: int = Field(..., gt=0)
    currency: Currency
    correlation_id: str
    description: str
    idempotency_key: Optional[str] = None


class TransferResponse(BaseModel):
    status: str
    journal_id: str
    from_balance: int
    to_balance: int


# Payment schemas
class PaymentInitiateRequest(BaseModel):
    provider: PaymentProvider
    amount_minor: int = Field(..., gt=0)
    currency: Currency
    order_id: Optional[str] = None
    invoice_id: Optional[uuid.UUID] = None
    idempotency_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    provider: str
    amount_minor: int
    currency: str
    created_at: str


class WithdrawalRequest(BaseModel):
    provider: PaymentProvider
    amount_minor: int = Field(..., gt=0)
    currency: Currency
    idempotency_key: Optional[str] = None


class WithdrawalResponse(BaseModel):
    withdrawal_id: str
    status: str
    approval_status: str
    amount_minor: int
    currency: str
    created_at: str


# Subscription schemas
class SubscriptionCreateRequest(BaseModel):
    plan: SubscriptionPlan
    currency: Currency
    billing_period: Optional[str] = "MONTHLY"


class SubscriptionUpgradeRequest(BaseModel):
    new_plan: SubscriptionPlan


class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan: str
    status: str
    current_period_end: str
    auto_renew: bool
