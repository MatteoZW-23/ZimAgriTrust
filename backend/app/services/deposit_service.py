"""
Deposit service — pre-funding the buyer wallet from external sources.

Responsibilities:
  - Per-tier deposit limit enforcement (mirrors withdrawal limits).
  - Large-deposit ID-verification gate (>$1000 by default).
  - Channel-specific intent creation:
      * EcoCash / OneMoney → returns USSD push payload + intent
      * Bank transfer       → returns bank reference; manual reconciliation
      * Cash (agent)        → reserves intent for an authorised agent to collect
  - Idempotent confirmation by external_reference (prevents double-credit).
  - Deposits land in `Transaction(type=DEPOSIT)` and credit `wallet_service.deposit`.
  - Audit chain entry on every state change.
  - Refund window: 7 days from intent.created_at; refundable_until is set on
    completion if no funds have been spent yet.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.deposits import (
    DepositChannel,
    DepositIntent,
    DepositIntentStatus,
    DepositLimit,
    PaymentMethod,
)
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import notification_triggers
from app.services.audit_chain_service import append_audit
from app.services.transaction_signing_service import sign_transaction
from app.services.wallet_service import wallet_service
from app.services.withdrawal_limits_service import resolve_user_tier

logger = logging.getLogger(__name__)


REFUND_WINDOW_DAYS = 7
REFUND_FEE_PERCENT = 0.02   # 2% refund fee on unused deposits
REFUND_FEE_CAP_USD = 10.0


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

def _get_deposit_limits(db: Session, tier_value: str) -> dict[str, float]:
    row = db.query(DepositLimit).filter(DepositLimit.user_tier == tier_value).first()
    if row:
        return {
            "daily": float(row.daily_limit),
            "weekly": float(row.weekly_limit),
            "monthly": float(row.monthly_limit),
            "per_txn": float(row.per_transaction_limit),
            "id_verification_above": float(row.id_verification_required_above),
        }
    return {
        "daily": 500.0, "weekly": 1000.0, "monthly": 5000.0,
        "per_txn": 500.0, "id_verification_above": 1000.0,
    }


def _sum_deposits_since(db: Session, user_id, since: datetime) -> float:
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.DEPOSIT,
            Transaction.status == "completed",
            Transaction.created_at >= since,
        )
        .scalar()
    )
    return float(total or 0.0)


def get_deposit_usage(db: Session, user: User) -> dict[str, float]:
    now = datetime.now(timezone.utc)
    return {
        "today_amount": _sum_deposits_since(db, user.id, now - timedelta(days=1)),
        "week_amount": _sum_deposits_since(db, user.id, now - timedelta(days=7)),
        "month_amount": _sum_deposits_since(db, user.id, now - timedelta(days=30)),
    }


def check_deposit_allowed(
    db: Session,
    *,
    user: User,
    amount: float,
    currency: str = "USD",
) -> dict:
    """Pre-flight checks. Raises HTTPException(400) on violation."""
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if amount < settings.DEPOSIT_MIN_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum deposit is ${settings.DEPOSIT_MIN_AMOUNT:.2f}",
        )
    if currency != "USD":
        raise HTTPException(status_code=400, detail="Only USD deposits supported")

    tier = resolve_user_tier(user)
    limits = _get_deposit_limits(db, tier.value)
    usage = get_deposit_usage(db, user)

    if amount > limits["per_txn"]:
        raise HTTPException(
            status_code=400,
            detail=f"Per-deposit limit ${limits['per_txn']:.2f} for tier {tier.value}",
        )
    if usage["today_amount"] + amount > limits["daily"]:
        raise HTTPException(
            status_code=400,
            detail=f"Daily deposit cap exceeded ({usage['today_amount']:.2f}/{limits['daily']:.2f})",
        )
    if usage["week_amount"] + amount > limits["weekly"]:
        raise HTTPException(
            status_code=400,
            detail=f"Weekly deposit cap exceeded ({usage['week_amount']:.2f}/{limits['weekly']:.2f})",
        )

    # ID-verification gate for large deposits
    requires_id = False
    if amount > limits["id_verification_above"]:
        if not getattr(user, "is_id_verified", False):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "ID_VERIFICATION_REQUIRED",
                    "message": f"Deposits over ${limits['id_verification_above']:.0f} require verified ID. "
                               "Upload your ID before continuing.",
                },
            )
        requires_id = True

    return {
        "amount": round(amount, 2),
        "currency": currency,
        "tier": tier.value,
        "limits": limits,
        "usage": usage,
        "requires_id_verification": requires_id,
    }


# ---------------------------------------------------------------------------
# Intent creation
# ---------------------------------------------------------------------------

def _new_intent(
    db: Session,
    *,
    user: User,
    channel: DepositChannel,
    amount: float,
    currency: str,
    payment_method_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None,
    requires_id_verification: bool = False,
) -> DepositIntent:
    intent = DepositIntent(
        user_id=user.id,
        channel=channel,
        payment_method_id=payment_method_id,
        amount=Decimal(str(amount)),
        currency=currency,
        status=DepositIntentStatus.PENDING,
        nonce=secrets.token_hex(16),
        external_reference=f"AGT-{secrets.token_hex(6).upper()}",
        metadata_json=metadata,
        requires_id_verification=requires_id_verification,
    )
    db.add(intent)
    db.flush()
    append_audit(
        db,
        table_name="deposit_intents",
        record_id=str(intent.id),
        operation="CREATE",
        payload={
            "user_id": str(user.id),
            "channel": channel.value,
            "amount": float(amount),
            "currency": currency,
            "external_reference": intent.external_reference,
        },
        actor_id=str(user.id),
        actor_role=user.role.value,
    )
    return intent


def initiate_mobile_money(
    db: Session,
    *,
    user: User,
    channel: DepositChannel,
    amount: float,
    msisdn: str,
    currency: str = "USD",
    payment_method_id: Optional[uuid.UUID] = None,
) -> dict:
    """Mobile money deposit. Returns intent + push payload for the gateway."""
    if channel not in (DepositChannel.ECOCASH, DepositChannel.ONEMONEY, DepositChannel.INNBUCKS, DepositChannel.OMARI):
        raise HTTPException(status_code=400, detail="Unsupported channel for mobile money flow")
    pre = check_deposit_allowed(db, user=user, amount=amount, currency=currency)

    intent = _new_intent(
        db, user=user, channel=channel, amount=amount, currency=currency,
        payment_method_id=payment_method_id,
        metadata={"msisdn_last4": msisdn[-4:] if msisdn else None},
        requires_id_verification=pre["requires_id_verification"],
    )
    db.commit()

    # Real implementation calls the provider SDK; for MVP we return the push payload.
    push = {
        "provider": channel.value,
        "msisdn": msisdn,
        "amount": float(amount),
        "currency": currency,
        "reference": intent.external_reference,
    }
    return {"intent_id": str(intent.id), "status": intent.status.value, "push": push}


def initiate_bank_transfer(
    db: Session,
    *,
    user: User,
    amount: float,
    payment_method_id: Optional[uuid.UUID] = None,
    currency: str = "USD",
) -> dict:
    """Bank transfer. Returns destination + reference; reconciliation is manual / nightly."""
    pre = check_deposit_allowed(db, user=user, amount=amount, currency=currency)
    intent = _new_intent(
        db, user=user, channel=DepositChannel.BANK_TRANSFER, amount=amount, currency=currency,
        payment_method_id=payment_method_id,
        requires_id_verification=pre["requires_id_verification"],
    )
    intent.bank_reference = intent.external_reference
    db.commit()
    return {
        "intent_id": str(intent.id),
        "status": intent.status.value,
        "instructions": {
            "bank_name": settings.PARTNER_BANK_NAME,
            "account_name": settings.PARTNER_BANK_ACCOUNT_NAME,
            "account_number": settings.PARTNER_BANK_ACCOUNT_NUMBER,
            "branch_code": settings.PARTNER_BANK_BRANCH_CODE,
            "reference": intent.external_reference,
            "amount": float(amount),
            "currency": currency,
            "expected_clearing_hours": 24,
        },
    }


def initiate_cash_via_agent(
    db: Session,
    *,
    user: User,
    amount: float,
    agent_id: Optional[uuid.UUID] = None,
    currency: str = "USD",
) -> dict:
    """Cash via agent. Buyer hands cash to agent; agent confirms collection."""
    pre = check_deposit_allowed(db, user=user, amount=amount, currency=currency)
    intent = _new_intent(
        db, user=user, channel=DepositChannel.CASH_AGENT, amount=amount, currency=currency,
        metadata={"requested_agent_id": str(agent_id) if agent_id else None},
        requires_id_verification=pre["requires_id_verification"],
    )
    db.commit()
    return {
        "intent_id": str(intent.id),
        "status": intent.status.value,
        "reference": intent.external_reference,
        "instructions": (
            f"Visit any verified agent. Show reference {intent.external_reference} "
            f"and pay ${amount:.2f}. Funds land in your wallet within 30 minutes."
        ),
    }


# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------

def confirm_intent(
    db: Session,
    *,
    intent_id: uuid.UUID,
    external_reference: Optional[str] = None,
    actor: Optional[User] = None,
) -> DepositIntent:
    """
    Idempotent confirmation. Credits the user's wallet exactly once.
    Called by:
      - mobile-money provider webhook
      - bank-transfer reconciliation cron
      - agent collection endpoint (after agent_collected_at recorded)
    """
    intent = db.query(DepositIntent).filter(DepositIntent.id == intent_id).with_for_update().first()
    if not intent:
        raise HTTPException(status_code=404, detail="Deposit intent not found")
    if intent.status == DepositIntentStatus.COMPLETED:
        return intent  # idempotent
    if intent.status not in (DepositIntentStatus.PENDING, DepositIntentStatus.AGENT_HELD):
        raise HTTPException(status_code=400, detail=f"Cannot confirm intent in state {intent.status.value}")

    if external_reference and intent.external_reference != external_reference:
        raise HTTPException(status_code=400, detail="External reference mismatch")

    user = db.query(User).filter(User.id == intent.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Owner not found")

    # Sign the deposit transaction
    signature, signed_payload = sign_transaction(
        user_id=str(user.id),
        txn_type=TransactionType.DEPOSIT.value,
        amount=float(intent.amount),
        currency=intent.currency,
        nonce=intent.nonce,
        extra={"channel": intent.channel.value, "intent_id": str(intent.id)},
    )

    # Credit wallet (creates Transaction row internally)
    ok = wallet_service.deposit(db, user.id, float(intent.amount), intent.currency, str(intent.id))
    if not ok:
        intent.status = DepositIntentStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail="Wallet credit failed")

    txn = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.DEPOSIT,
        )
        .order_by(Transaction.created_at.desc())
        .first()
    )

    intent.status = DepositIntentStatus.COMPLETED
    intent.transaction_id = txn.id if txn else None
    intent.completed_at = datetime.now(timezone.utc)
    intent.refundable_until = datetime.now(timezone.utc) + timedelta(days=REFUND_WINDOW_DAYS)
    intent.receipt_url = f"/api/v1/deposits/{intent.id}/receipt"

    append_audit(
        db,
        table_name="deposit_intents",
        record_id=str(intent.id),
        operation="COMPLETE",
        payload={
            "user_id": str(user.id),
            "amount": float(intent.amount),
            "currency": intent.currency,
            "channel": intent.channel.value,
            "external_reference": intent.external_reference,
            "transaction_id": str(intent.transaction_id) if intent.transaction_id else None,
            "signature": signature,
            "signed_payload": signed_payload,
        },
        actor_id=str(actor.id) if actor else str(user.id),
        actor_role=actor.role.value if actor else user.role.value,
    )
    db.commit()
    notification_triggers.deposit_completed(
        getattr(user, "phone_number", None),
        float(intent.amount),
        intent.channel.value,
        intent.external_reference or str(intent.id),
    )
    return intent


def fail_intent(db: Session, *, intent_id: uuid.UUID, reason: str) -> DepositIntent:
    intent = db.query(DepositIntent).filter(DepositIntent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Deposit intent not found")
    if intent.status == DepositIntentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Already completed")
    intent.status = DepositIntentStatus.FAILED
    intent.metadata_json = {**(intent.metadata_json or {}), "failure_reason": reason}
    append_audit(
        db,
        table_name="deposit_intents",
        record_id=str(intent.id),
        operation="FAIL",
        payload={"reason": reason},
        actor_id=str(intent.user_id),
    )
    db.commit()
    user = db.query(User).filter(User.id == intent.user_id).first()
    if user:
        notification_triggers.deposit_failed(
            getattr(user, "phone_number", None), reason, intent.external_reference or str(intent.id)
        )
    return intent


# ---------------------------------------------------------------------------
# Cash-via-agent steps
# ---------------------------------------------------------------------------

def agent_collect_cash(
    db: Session,
    *,
    intent_id: uuid.UUID,
    agent: User,
    receipt_no: str,
) -> DepositIntent:
    """Agent records that they have collected the cash. Funds NOT yet credited."""
    intent = db.query(DepositIntent).filter(DepositIntent.id == intent_id).with_for_update().first()
    if not intent:
        raise HTTPException(status_code=404, detail="Deposit intent not found")
    if intent.channel != DepositChannel.CASH_AGENT:
        raise HTTPException(status_code=400, detail="Not a cash-agent intent")
    if intent.status != DepositIntentStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Intent is {intent.status.value}")

    intent.agent_id = agent.id
    intent.agent_collected_at = datetime.now(timezone.utc)
    intent.agent_receipt_no = receipt_no
    intent.status = DepositIntentStatus.AGENT_HELD
    append_audit(
        db,
        table_name="deposit_intents",
        record_id=str(intent.id),
        operation="AGENT_COLLECT",
        payload={"agent_id": str(agent.id), "receipt_no": receipt_no},
        actor_id=str(agent.id),
        actor_role=agent.role.value,
    )
    db.commit()
    buyer = db.query(User).filter(User.id == intent.user_id).first()
    agent_name = getattr(agent, "full_name", None) or getattr(agent, "phone_number", "agent")
    if buyer:
        notification_triggers.cash_collected_by_agent(
            getattr(buyer, "phone_number", None), agent_name, float(intent.amount)
        )
    return intent


def agent_reconcile_cash(
    db: Session,
    *,
    intent_id: uuid.UUID,
    agent: User,
) -> DepositIntent:
    """Agent (or admin) confirms cash deposited at the partner bank → credit wallet."""
    intent = db.query(DepositIntent).filter(DepositIntent.id == intent_id).first()
    if not intent or intent.channel != DepositChannel.CASH_AGENT:
        raise HTTPException(status_code=404, detail="Cash-agent intent not found")
    if intent.status != DepositIntentStatus.AGENT_HELD:
        raise HTTPException(status_code=400, detail="Cash not yet collected")
    intent.agent_reconciled_at = datetime.now(timezone.utc)
    return confirm_intent(db, intent_id=intent.id, actor=agent)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

# Notification helpers live in app.services.notification_triggers
