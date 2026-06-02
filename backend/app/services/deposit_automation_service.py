"""Deposit automation service - auto-deposit rules and recurring deposits.

Implements auto top-up rules, recurring deposit schedules, and refund management.
"""
import logging
import uuid
import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.deposits import (
    AutoDepositRule,
    RecurringDepositSchedule,
    DepositRefundRequest,
    RefundStatus,
    RecurrenceCadence,
)
from app.models.user import User

logger = logging.getLogger(__name__)


def calculate_refund_fee(amount: float) -> float:
    """Refund processing fee: 2% capped at $10."""
    if amount <= 0:
        return 0.0
    return round(min(amount * 0.02, 10.0), 2)


def _next_run(
    cadence: RecurrenceCadence,
    day_of_week: Optional[int],
    day_of_month: Optional[int],
    from_dt: Optional[datetime] = None,
) -> datetime:
    """Calculate the next recurring deposit date after ``from_dt``."""
    base = from_dt or datetime.now(timezone.utc)
    cadence_value = cadence.value if isinstance(cadence, RecurrenceCadence) else str(cadence).lower()

    if cadence_value == RecurrenceCadence.WEEKLY.value:
        target_day = base.weekday() if day_of_week is None else max(0, min(6, int(day_of_week)))
        days_ahead = (target_day - base.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return base + timedelta(days=days_ahead)

    if cadence_value == RecurrenceCadence.BIWEEKLY.value:
        return base + timedelta(days=14)

    target_day = 28 if day_of_month is None else max(1, min(28, int(day_of_month)))
    year = base.year + (1 if base.month == 12 else 0)
    month = 1 if base.month == 12 else base.month + 1
    day = min(target_day, calendar.monthrange(year, month)[1], 28)
    next_dt = base.replace(year=year, month=month, day=day)
    if next_dt <= base:
        year = next_dt.year + (1 if next_dt.month == 12 else 0)
        month = 1 if next_dt.month == 12 else next_dt.month + 1
        day = min(target_day, calendar.monthrange(year, month)[1], 28)
        next_dt = next_dt.replace(year=year, month=month, day=day)
    return next_dt


def upsert_auto_rule(
    db: Session,
    user: User,
    payment_method_id: str,
    threshold: float,
    top_up_amount: float,
) -> AutoDepositRule:
    """Create or update auto-deposit rule."""
    logger.info(f"Upsert auto rule for user {user.id}: threshold={threshold}, amount={top_up_amount}")
    
    # Check if rule exists
    existing = db.query(AutoDepositRule).filter(
        AutoDepositRule.user_id == user.id
    ).first()
    
    if existing:
        existing.payment_method_id = payment_method_id
        existing.threshold_usd = threshold
        existing.topup_amount_usd = top_up_amount
        existing.is_active = True
    else:
        existing = AutoDepositRule(
            user_id=user.id,
            payment_method_id=payment_method_id,
            threshold_usd=threshold,
            topup_amount_usd=top_up_amount,
            is_active=True,
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing


def disable_auto_rule(db: Session, user: User) -> None:
    """Disable auto-deposit rule for user."""
    logger.info(f"Disable auto rule for user {user.id}")
    
    rule = db.query(AutoDepositRule).filter(
        AutoDepositRule.user_id == user.id
    ).first()
    
    if rule:
        rule.is_active = False
        db.commit()


def create_schedule(
    db: Session,
    user: User,
    payment_method_id: str,
    amount: float,
    cadence: str,
    start_date: str,
) -> RecurringDepositSchedule:
    """Create recurring deposit schedule."""
    logger.info(f"Create schedule for user {user.id}: amount={amount}, cadence={cadence}")
    
    # Parse start date
    try:
        start_dt = datetime.fromisoformat(start_date)
    except ValueError:
        start_dt = datetime.now(timezone.utc)
    
    # Validate cadence
    try:
        cadence_enum = RecurrenceCadence(cadence.lower())
    except ValueError:
        raise ValueError(f"Invalid cadence: {cadence}. Must be one of: weekly, biweekly, monthly")
    
    schedule = RecurringDepositSchedule(
        user_id=user.id,
        payment_method_id=payment_method_id,
        amount_usd=amount,
        cadence=cadence_enum,
        next_run_at=_next_run(cadence_enum, None, start_dt.day, start_dt),
        is_active=True,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def cancel_schedule(db: Session, user: User, schedule_id: str) -> None:
    """Cancel recurring deposit schedule."""
    logger.info(f"Cancel schedule {schedule_id} for user {user.id}")
    
    schedule = db.query(RecurringDepositSchedule).filter(
        RecurringDepositSchedule.id == uuid.UUID(schedule_id),
        RecurringDepositSchedule.user_id == user.id
    ).first()
    
    if schedule:
        schedule.is_active = False
        db.commit()


def request_refund(
    db: Session,
    user: User,
    intent_id: str,
    reason: str,
) -> DepositRefundRequest:
    """Request refund for deposit."""
    logger.info(f"Request refund for intent {intent_id} by user {user.id}: {reason}")
    
    from app.models.deposits import DepositIntent
    
    intent = db.query(DepositIntent).filter(
        DepositIntent.id == uuid.UUID(intent_id),
        DepositIntent.user_id == user.id
    ).first()
    
    if not intent:
        raise ValueError("Deposit intent not found")
    
    # Check if refund already requested
    existing = db.query(DepositRefundRequest).filter(
        DepositRefundRequest.deposit_intent_id == intent.id
    ).first()
    
    if existing:
        return existing
    
    refund_request = DepositRefundRequest(
        deposit_intent_id=intent.id,
        user_id=user.id,
        amount=float(intent.amount),
        fee=calculate_refund_fee(float(intent.amount)),
        net_refund=round(float(intent.amount) - calculate_refund_fee(float(intent.amount)), 2),
        reason=reason,
        status=RefundStatus.PENDING,
    )
    db.add(refund_request)
    db.commit()
    db.refresh(refund_request)
    return refund_request


def decide_refund(
    db: Session,
    request_id: str,
    actor: User,
    approve: bool,
    notes: Optional[str] = None,
) -> DepositRefundRequest:
    """Approve or reject refund request."""
    logger.info(f"Decide refund {request_id}: approve={approve}, by={actor.id}")
    
    refund_request = db.query(DepositRefundRequest).filter(
        DepositRefundRequest.id == uuid.UUID(request_id)
    ).first()
    
    if not refund_request:
        raise ValueError("Refund request not found")
    
    refund_request.status = RefundStatus.APPROVED if approve else RefundStatus.REJECTED
    refund_request.decided_by = actor.id
    refund_request.decided_at = datetime.now(timezone.utc)
    refund_request.decision_notes = notes
    
    db.commit()
    db.refresh(refund_request)
    return refund_request
