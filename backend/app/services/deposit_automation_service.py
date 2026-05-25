"""
Auto-deposit (top-up on threshold) + recurring schedule (weekly/monthly) +
refund-of-unused-funds service.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.deposits import (
    AutoDepositRule,
    DepositChannel,
    DepositIntent,
    DepositIntentStatus,
    DepositRefundRequest,
    PaymentMethod,
    RecurrenceCadence,
    RecurringDepositSchedule,
    RefundStatus,
)
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import deposit_service, notification_triggers
from app.services.audit_chain_service import append_audit
from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auto top-up (function 354)
# ---------------------------------------------------------------------------

def upsert_auto_rule(
    db: Session,
    *,
    user: User,
    payment_method_id: uuid.UUID,
    threshold_usd: float,
    topup_amount_usd: float,
) -> AutoDepositRule:
    if threshold_usd <= 0 or topup_amount_usd < settings.DEPOSIT_MIN_AMOUNT:
        raise HTTPException(status_code=400, detail="Invalid threshold/top-up amounts")
    pm = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id, PaymentMethod.user_id == user.id
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")
    if pm.channel == DepositChannel.CASH_AGENT:
        raise HTTPException(status_code=400, detail="Auto top-up requires a non-cash channel")

    rule = db.query(AutoDepositRule).filter(AutoDepositRule.user_id == user.id).first()
    if rule:
        rule.payment_method_id = payment_method_id
        rule.threshold_usd = Decimal(str(threshold_usd))
        rule.topup_amount_usd = Decimal(str(topup_amount_usd))
        rule.is_active = True
    else:
        rule = AutoDepositRule(
            user_id=user.id,
            payment_method_id=payment_method_id,
            threshold_usd=Decimal(str(threshold_usd)),
            topup_amount_usd=Decimal(str(topup_amount_usd)),
        )
        db.add(rule)
    db.flush()
    return rule


def disable_auto_rule(db: Session, *, user: User) -> None:
    rule = db.query(AutoDepositRule).filter(AutoDepositRule.user_id == user.id).first()
    if rule:
        rule.is_active = False


def maybe_trigger_auto_topup(db: Session, *, user: User) -> Optional[DepositIntent]:
    """Call this after any wallet debit. If balance fell below threshold, top up."""
    rule = (
        db.query(AutoDepositRule)
        .filter(AutoDepositRule.user_id == user.id, AutoDepositRule.is_active.is_(True))
        .first()
    )
    if not rule:
        return None
    balance = float(getattr(user, "balance_usd", 0) or 0)
    if balance >= float(rule.threshold_usd):
        return None

    # Daily cap on auto top-ups
    since = datetime.now(timezone.utc) - timedelta(days=1)
    today_count = (
        db.query(func.count(DepositIntent.id))
        .filter(
            DepositIntent.user_id == user.id,
            DepositIntent.created_at >= since,
            DepositIntent.metadata_json["auto"].astext == "1",
        )
        .scalar()
        or 0
    )
    if today_count >= rule.daily_max_topups:
        return None

    pm = db.query(PaymentMethod).filter(PaymentMethod.id == rule.payment_method_id).first()
    if not pm:
        return None

    amount = float(rule.topup_amount_usd)
    try:
        if pm.channel in (DepositChannel.ECOCASH, DepositChannel.ONEMONEY):
            result = deposit_service.initiate_mobile_money(
                db, user=user, channel=pm.channel, amount=amount,
                msisdn=pm.last4 or "", payment_method_id=pm.id,
            )
        elif pm.channel == DepositChannel.BANK_TRANSFER:
            result = deposit_service.initiate_bank_transfer(
                db, user=user, amount=amount, payment_method_id=pm.id,
            )
        else:
            return None
    except HTTPException:
        return None

    intent = db.query(DepositIntent).filter(DepositIntent.id == uuid.UUID(result["intent_id"])).first()
    if intent is not None:
        intent.metadata_json = {**(intent.metadata_json or {}), "auto": "1"}
    rule.last_triggered_at = datetime.now(timezone.utc)
    db.flush()
    return intent


# ---------------------------------------------------------------------------
# Recurring deposit schedule (function 355)
# ---------------------------------------------------------------------------

def _next_run(cadence: RecurrenceCadence, *, day_of_week: Optional[int],
              day_of_month: Optional[int], from_dt: Optional[datetime] = None) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    if cadence == RecurrenceCadence.WEEKLY:
        days = (day_of_week if day_of_week is not None else base.weekday()) - base.weekday()
        if days <= 0:
            days += 7
        return base + timedelta(days=days)
    if cadence == RecurrenceCadence.BIWEEKLY:
        return base + timedelta(days=14)
    if cadence == RecurrenceCadence.MONTHLY:
        target_day = day_of_month or 1
        # naive: jump 30 days, then snap to target day
        nxt = base + timedelta(days=30)
        try:
            return nxt.replace(day=min(target_day, 28))
        except ValueError:
            return nxt
    return base + timedelta(days=7)


def create_schedule(
    db: Session,
    *,
    user: User,
    payment_method_id: uuid.UUID,
    amount_usd: float,
    cadence: RecurrenceCadence,
    day_of_week: Optional[int] = None,
    day_of_month: Optional[int] = None,
) -> RecurringDepositSchedule:
    if amount_usd < settings.DEPOSIT_MIN_AMOUNT:
        raise HTTPException(status_code=400, detail="Amount below minimum")
    pm = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id, PaymentMethod.user_id == user.id
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")

    sched = RecurringDepositSchedule(
        user_id=user.id,
        payment_method_id=payment_method_id,
        amount_usd=Decimal(str(amount_usd)),
        cadence=cadence,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        next_run_at=_next_run(cadence, day_of_week=day_of_week, day_of_month=day_of_month),
    )
    db.add(sched)
    db.flush()
    return sched


def cancel_schedule(db: Session, *, user: User, schedule_id: uuid.UUID) -> None:
    sched = db.query(RecurringDepositSchedule).filter(
        RecurringDepositSchedule.id == schedule_id,
        RecurringDepositSchedule.user_id == user.id,
    ).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    sched.is_active = False


def run_due_schedules(db: Session, *, now: Optional[datetime] = None) -> int:
    """Scheduler entrypoint. Returns number of intents created."""
    now = now or datetime.now(timezone.utc)
    due = (
        db.query(RecurringDepositSchedule)
        .filter(
            RecurringDepositSchedule.is_active.is_(True),
            RecurringDepositSchedule.next_run_at <= now,
        )
        .all()
    )
    created = 0
    for sched in due:
        user = db.query(User).filter(User.id == sched.user_id).first()
        pm = db.query(PaymentMethod).filter(PaymentMethod.id == sched.payment_method_id).first()
        if not user or not pm or not user.is_active:
            sched.consecutive_failures += 1
            continue
        try:
            if pm.channel in (DepositChannel.ECOCASH, DepositChannel.ONEMONEY):
                deposit_service.initiate_mobile_money(
                    db, user=user, channel=pm.channel, amount=float(sched.amount_usd),
                    msisdn=pm.last4 or "", payment_method_id=pm.id,
                )
            elif pm.channel == DepositChannel.BANK_TRANSFER:
                deposit_service.initiate_bank_transfer(
                    db, user=user, amount=float(sched.amount_usd), payment_method_id=pm.id,
                )
            else:
                sched.consecutive_failures += 1
                continue
            sched.consecutive_failures = 0
            created += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Recurring deposit failed user=%s sched=%s: %s", user.id, sched.id, exc)
            sched.consecutive_failures += 1

        sched.last_run_at = now
        sched.next_run_at = _next_run(
            sched.cadence,
            day_of_week=sched.day_of_week,
            day_of_month=sched.day_of_month,
            from_dt=now,
        )
        if sched.consecutive_failures >= 5:
            sched.is_active = False
    db.commit()
    return created


# ---------------------------------------------------------------------------
# Deposit refund (function 357)
# ---------------------------------------------------------------------------

def calculate_refund_fee(amount: float) -> float:
    raw = amount * settings.DEPOSIT_REFUND_FEE_PERCENT
    return round(min(raw, settings.DEPOSIT_REFUND_FEE_CAP), 2)


def request_refund(
    db: Session,
    *,
    user: User,
    intent_id: uuid.UUID,
    reason: Optional[str] = None,
) -> DepositRefundRequest:
    intent = db.query(DepositIntent).filter(
        DepositIntent.id == intent_id, DepositIntent.user_id == user.id
    ).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Deposit not found")
    if intent.status != DepositIntentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed deposits are refundable")
    if not intent.refundable_until or datetime.now(timezone.utc) > intent.refundable_until:
        raise HTTPException(status_code=400, detail="7-day refund window has expired")

    # Available balance must cover the refund (no funds were spent)
    available = float(getattr(user, "balance_usd", 0) or 0)
    if available < float(intent.amount):
        raise HTTPException(
            status_code=400,
            detail=f"Refund only available for unused funds (available ${available:.2f}, deposit ${float(intent.amount):.2f})",
        )

    # One refund request per intent
    existing = db.query(DepositRefundRequest).filter(
        DepositRefundRequest.deposit_intent_id == intent_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Refund already {existing.status.value}")

    fee = calculate_refund_fee(float(intent.amount))
    net = round(float(intent.amount) - fee, 2)
    req = DepositRefundRequest(
        deposit_intent_id=intent.id,
        user_id=user.id,
        amount=intent.amount,
        fee=Decimal(str(fee)),
        net_refund=Decimal(str(net)),
        reason=reason,
    )
    db.add(req)
    intent.status = DepositIntentStatus.REFUND_REQUESTED
    db.flush()
    return req


def decide_refund(
    db: Session,
    *,
    request_id: uuid.UUID,
    actor: User,
    approve: bool,
    notes: Optional[str] = None,
) -> DepositRefundRequest:
    req = db.query(DepositRefundRequest).filter(DepositRefundRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Refund request not found")
    if req.status != RefundStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request already {req.status.value}")

    req.decided_by = actor.id
    req.decided_at = datetime.now(timezone.utc)
    req.decision_notes = notes
    intent = db.query(DepositIntent).filter(DepositIntent.id == req.deposit_intent_id).first()

    if not approve:
        req.status = RefundStatus.REJECTED
        if intent:
            intent.status = DepositIntentStatus.COMPLETED
        db.flush()
        return req

    # Approve → debit wallet, mark processed
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Owner not found")
    debit_ok = wallet_service.withdraw(db, user.id, float(req.amount), "USD")
    if not debit_ok:
        req.status = RefundStatus.REJECTED
        req.decision_notes = (notes or "") + " | auto-rejected: insufficient balance"
        if intent:
            intent.status = DepositIntentStatus.COMPLETED
        db.flush()
        return req

    req.status = RefundStatus.PROCESSED
    req.processed_at = datetime.now(timezone.utc)
    if intent:
        intent.status = DepositIntentStatus.REFUNDED

    append_audit(
        db,
        table_name="deposit_refund_requests",
        record_id=str(req.id),
        operation="REFUND_PROCESSED",
        payload={
            "user_id": str(user.id),
            "amount": float(req.amount),
            "fee": float(req.fee),
            "net": float(req.net_refund),
            "intent_id": str(req.deposit_intent_id),
        },
        actor_id=str(actor.id),
        actor_role=actor.role.value,
    )
    db.flush()
    notification_triggers.deposit_refund_processed(
        getattr(user, "phone_number", None), float(req.net_refund), float(req.fee),
    )
    return req
