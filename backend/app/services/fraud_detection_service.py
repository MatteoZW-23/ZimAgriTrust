"""
Fraud detection for cash operations.

Flags raised:
  - VELOCITY            : multiple withdrawals in short window
  - STRUCTURING         : amount just below tier limit
  - NEW_USER_LARGE_WITHDRAWAL
  - DUPLICATE_BANK_DETAILS  (multiple users sharing bank/mobile money fingerprint)
  - TRUST_SCORE_SPIKE   (sudden trust increase without transactions)

On HIGH/CRITICAL alerts, an SMS is sent to the configured super-admin phone.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import (
    FraudAlert,
    FraudAlertType,
    FraudSeverity,
)
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services.withdrawal_limits_service import (
    get_tier_limits,
    is_structuring_amount,
    resolve_user_tier,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_withdrawal(
    db: Session,
    *,
    user: User,
    amount: float,
    bank_fingerprint: Optional[str] = None,
) -> list[FraudAlert]:
    """Run ALL withdrawal-time fraud checks. Returns alerts created."""
    alerts: list[FraudAlert] = []
    alerts += _check_velocity(db, user)
    alerts += _check_structuring(db, user, amount)
    alerts += _check_new_user_large_withdrawal(db, user, amount)
    if bank_fingerprint:
        alerts += _check_duplicate_bank(db, user, bank_fingerprint)
    if alerts:
        db.flush()
        _notify_super_admin(alerts)
    return alerts


def evaluate_trust_score_change(
    db: Session,
    *,
    user: User,
    old_score: int,
    new_score: int,
) -> Optional[FraudAlert]:
    """Call this from trust_service whenever a user's trust score changes."""
    delta = new_score - old_score
    if delta < settings.FRAUD_TRUST_SCORE_SPIKE_THRESHOLD:
        return None

    # Did the user have any successful transactions to justify the spike?
    has_txn = (
        db.query(Transaction.id)
        .filter(
            Transaction.user_id == user.id,
            Transaction.status == "completed",
            Transaction.type.in_([TransactionType.PAYMENT, TransactionType.ESCROW_RELEASE]),
        )
        .first()
    )
    if has_txn:
        return None

    alert = _record_alert(
        db,
        user_id=user.id,
        alert_type=FraudAlertType.TRUST_SCORE_SPIKE,
        severity=FraudSeverity.HIGH,
        details={"old_score": old_score, "new_score": new_score, "delta": delta},
    )
    db.flush()
    _notify_super_admin([alert])
    return alert


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_velocity(db: Session, user: User) -> list[FraudAlert]:
    since = datetime.now(timezone.utc) - timedelta(seconds=settings.FRAUD_VELOCITY_WINDOW_SECONDS)
    count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.WITHDRAWAL,
            Transaction.status != "failed",
            Transaction.created_at >= since,
        )
        .scalar()
        or 0
    )
    if count >= settings.FRAUD_VELOCITY_THRESHOLD:
        return [
            _record_alert(
                db,
                user_id=user.id,
                alert_type=FraudAlertType.VELOCITY,
                severity=FraudSeverity.HIGH,
                details={
                    "withdrawals_in_window": int(count),
                    "window_seconds": settings.FRAUD_VELOCITY_WINDOW_SECONDS,
                },
            )
        ]
    return []


def _check_structuring(db: Session, user: User, amount: float) -> list[FraudAlert]:
    tier = resolve_user_tier(user)
    limits = get_tier_limits(db, tier)
    if is_structuring_amount(amount, limits["daily"]):
        return [
            _record_alert(
                db,
                user_id=user.id,
                alert_type=FraudAlertType.STRUCTURING,
                severity=FraudSeverity.MEDIUM,
                details={
                    "amount": amount,
                    "daily_limit": limits["daily"],
                    "tier": tier.value,
                },
            )
        ]
    return []


def _check_new_user_large_withdrawal(db: Session, user: User, amount: float) -> list[FraudAlert]:
    created_at = getattr(user, "created_at", None)
    if not created_at:
        return []
    age = datetime.now(timezone.utc) - (
        created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    )
    if age <= timedelta(days=settings.FRAUD_NEW_USER_DAYS) and amount >= settings.FRAUD_NEW_USER_LARGE_WITHDRAWAL_USD:
        return [
            _record_alert(
                db,
                user_id=user.id,
                alert_type=FraudAlertType.NEW_USER_LARGE_WITHDRAWAL,
                severity=FraudSeverity.HIGH,
                details={
                    "amount": amount,
                    "account_age_days": age.days,
                },
            )
        ]
    return []


def _check_duplicate_bank(db: Session, user: User, bank_fingerprint: str) -> list[FraudAlert]:
    """
    Detect multiple users sharing a bank/mobile-money fingerprint.

    A `bank_fingerprint` is a stable hash of (account_number + bank_code) or
    (mobile_money_number) — caller computes it. We look up other users.
    """
    # The current schema does not yet store fingerprints on User. Keep this as a
    # service-level extension point: callers that DO have fingerprint storage
    # invoke it. For now we treat any fingerprint match as a soft signal.
    matches = (
        db.query(User.id)
        .filter(User.bank_fingerprint == bank_fingerprint, User.id != user.id)
        if hasattr(User, "bank_fingerprint")
        else None
    )
    if matches is None:
        return []
    other_ids = [str(uid) for (uid,) in matches.limit(5).all()]
    if not other_ids:
        return []
    return [
        _record_alert(
            db,
            user_id=user.id,
            alert_type=FraudAlertType.DUPLICATE_BANK_DETAILS,
            severity=FraudSeverity.CRITICAL,
            details={"bank_fingerprint": bank_fingerprint, "other_user_ids": other_ids},
        )
    ]


# ---------------------------------------------------------------------------
# Alert recording + notification
# ---------------------------------------------------------------------------

def _record_alert(
    db: Session,
    *,
    user_id,
    alert_type: FraudAlertType,
    severity: FraudSeverity,
    details: dict[str, Any],
    related_resource_type: Optional[str] = None,
    related_resource_id: Optional[str] = None,
) -> FraudAlert:
    alert = FraudAlert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        details=details,
        related_resource_type=related_resource_type,
        related_resource_id=related_resource_id,
        resolved=False,
        notified_super_admin=False,
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    return alert


def _notify_super_admin(alerts: list[FraudAlert]) -> None:
    """Best-effort SMS notification for HIGH/CRITICAL alerts. Never raises."""
    phone = settings.SUPER_ADMIN_ALERT_PHONE
    if not phone:
        return
    for alert in alerts:
        if alert.severity not in (FraudSeverity.HIGH, FraudSeverity.CRITICAL):
            continue
        try:
            from app.services.sms_service import sms_service  # local import to avoid cycle
            msg = (
                f"[ZimAgriTrust ALERT] {alert.severity.value.upper()} {alert.alert_type.value} "
                f"user={alert.user_id} details={alert.details}"
            )
            sms_service.send_sms(phone, msg)  # type: ignore[attr-defined]
            alert.notified_super_admin = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fraud alert SMS failed: %s", exc)


def list_open_alerts(db: Session, *, severity: Optional[FraudSeverity] = None, limit: int = 100):
    q = db.query(FraudAlert).filter(FraudAlert.resolved.is_(False))
    if severity:
        q = q.filter(FraudAlert.severity == severity)
    return q.order_by(FraudAlert.created_at.desc()).limit(limit).all()


def resolve_alert(
    db: Session,
    *,
    alert_id,
    super_admin_id: int,
    notes: Optional[str] = None,
) -> FraudAlert:
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise ValueError("alert not found")
    alert.resolved = True
    alert.resolved_by = super_admin_id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = notes
    db.flush()
    return alert
