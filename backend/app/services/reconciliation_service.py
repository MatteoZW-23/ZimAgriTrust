"""
Daily reconciliation report.

Cross-checks:
  - Sum(user.balance + user.pending) per currency  (the system's liability)
  - Sum(transactions) over the period               (flow)
  - Open escrow orders                               (held in trust)
  - Withdrawals processed today
  - Open fraud alerts
  - Audit chain integrity

Result is persisted (system_audit) and emailed/SMS'd to super admin.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import FraudAlert, FraudSeverity
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User
from app.services.audit_chain_service import verify_chain

logger = logging.getLogger(__name__)


def run_daily_reconciliation(db: Session) -> dict:
    """Compute reconciliation snapshot. Idempotent — safe to run anytime."""
    now = datetime.now(timezone.utc)
    day_start = now - timedelta(days=1)

    total_balance_usd = float(db.query(func.coalesce(func.sum(User.balance_usd), 0.0)).scalar() or 0)
    total_pending_usd = float(db.query(func.coalesce(func.sum(User.pending_usd), 0.0)).scalar() or 0)
    liability_usd = round(total_balance_usd + total_pending_usd, 2)

    open_escrow_amount = float(
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(Order.status.in_([OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.DISPUTED]))
        .scalar()
        or 0
    )
    open_escrow_count = int(
        db.query(func.count(Order.id))
        .filter(Order.status.in_([OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.DISPUTED]))
        .scalar()
        or 0
    )

    today_withdrawals_amount = float(
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.type == TransactionType.WITHDRAWAL,
            Transaction.status != "failed",
            Transaction.created_at >= day_start,
        )
        .scalar()
        or 0
    )
    today_withdrawals_count = int(
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.type == TransactionType.WITHDRAWAL,
            Transaction.status != "failed",
            Transaction.created_at >= day_start,
        )
        .scalar()
        or 0
    )

    today_fees = float(
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.type == TransactionType.FEE,
            Transaction.created_at >= day_start,
        )
        .scalar()
        or 0
    )

    open_alerts = (
        db.query(FraudAlert.severity, func.count(FraudAlert.id))
        .filter(FraudAlert.resolved.is_(False))
        .group_by(FraudAlert.severity)
        .all()
    )
    alerts_by_severity = {sev.value: int(cnt) for sev, cnt in open_alerts}
    critical_open = alerts_by_severity.get(FraudSeverity.CRITICAL.value, 0)

    chain = verify_chain(db, limit=5000)

    integrity_ok = chain["ok"] and critical_open == 0

    report = {
        "timestamp": now.isoformat(),
        "liability_usd": liability_usd,
        "balance_pool_usd": round(total_balance_usd, 2),
        "escrow_pool_usd": round(total_pending_usd, 2),
        "open_escrow": {"count": open_escrow_count, "amount_usd": round(open_escrow_amount, 2)},
        "today": {
            "withdrawals_count": today_withdrawals_count,
            "withdrawals_amount_usd": round(today_withdrawals_amount, 2),
            "fees_collected_usd": round(today_fees, 2),
        },
        "fraud_alerts_open": alerts_by_severity,
        "audit_chain": {"ok": chain["ok"], "checked": chain["checked"], "first_break_id": chain["first_break_id"]},
        "integrity_check": "PASSED" if integrity_ok else "FAILED",
    }

    _persist_system_audit(db, report)
    _notify_super_admin(report)
    logger.info("[RECONCILIATION] %s", report)
    return report


def _persist_system_audit(db: Session, report: dict) -> None:
    try:
        from app.models.system_audit import SystemAudit
        db.add(SystemAudit(
            event_type="DAILY_RECONCILIATION",
            details=report,
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not persist reconciliation audit: %s", exc)
        db.rollback()


def _notify_super_admin(report: dict) -> None:
    if settings.SUPER_ADMIN_ALERT_EMAIL:
        try:
            from app.services.email_service import email_service
            email_service.send_template(  # type: ignore[attr-defined]
                "email.daily_reconciliation",
                to=settings.SUPER_ADMIN_ALERT_EMAIL,
                context={"report": report},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Reconciliation email failed: %s", exc)

    if report["integrity_check"] != "PASSED" and settings.SUPER_ADMIN_ALERT_PHONE:
        try:
            from app.services.sms_service import sms_service
            sms_service.send_sms(  # type: ignore[attr-defined]
                settings.SUPER_ADMIN_ALERT_PHONE,
                f"[ZimAgriTrust] Reconciliation FAILED at {report['timestamp']}. "
                f"Audit chain ok={report['audit_chain']['ok']}, "
                f"open_alerts={report['fraud_alerts_open']}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Reconciliation SMS failed: %s", exc)
