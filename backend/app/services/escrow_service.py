"""
escrow_service.py — Production-hardened escrow state machine.

Critical invariants enforced here:
  1. All state-changing functions re-fetch the Order with SELECT FOR UPDATE
     so that concurrent callers serialise at the database row.
  2. State is re-validated AFTER the lock is acquired — not from the caller's
     stale in-memory object.
  3. All money movement goes through WalletService (ledger only).
     user.balance_usd / user.pending_usd are never touched directly.
  4. Every function issues exactly one db.commit() and rolls back on failure.
  5. process_auto_settlement enforces the 7-day timer from order.updated_at.
  6. release_payment is idempotent: calling it on a COMPLETED order returns
     the order without re-crediting.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.transaction import Order, OrderStatus, Transaction, TransactionType

AUTO_SETTLEMENT_DAYS = 7


def _lock_order(db: Session, order_id: uuid.UUID) -> Order:
    """
    Fetch order with a row-level exclusive lock (SELECT FOR UPDATE).
    Raises 404 if not found. Callers MUST re-validate state after this call.
    """
    locked = db.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    ).scalar_one_or_none()
    if not locked:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return locked


def verify_handover_code(order: Order, provided_code: str) -> bool:
    if not provided_code or not order.handover_code:
        return False
    return provided_code.strip().upper() == order.handover_code.strip().upper()


def hold_payment(db: Session, order: Order) -> Order:
    """
    Transition PENDING → ESCROW_HELD.
    Idempotent: already ESCROW_HELD returns the order unchanged.
    """
    locked = _lock_order(db, order.id)

    if locked.status == OrderStatus.ESCROW_HELD:
        return locked

    if locked.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be PENDING to hold escrow, current state: {locked.status}",
        )

    locked.status = OrderStatus.ESCROW_HELD
    db.commit()
    db.refresh(locked)
    return locked


def mark_delivered(db: Session, order: Order) -> Order:
    """
    Transition ESCROW_HELD → DELIVERED.
    Idempotent: already DELIVERED returns the order unchanged.
    """
    locked = _lock_order(db, order.id)

    if locked.status == OrderStatus.DELIVERED:
        return locked

    if locked.status != OrderStatus.ESCROW_HELD:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be ESCROW_HELD to mark delivered, current state: {locked.status}",
        )

    locked.status = OrderStatus.DELIVERED
    locked.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(locked)
    return locked


def release_payment(db: Session, order: Order, handover_code: str = None) -> Order:
    """
    Transition {ESCROW_HELD | DELIVERED | DISPUTED} → COMPLETED.

    Idempotent: already COMPLETED returns the order without re-crediting.

    Financial flow (via LedgerService, double-entry):
      PENDING_ESCROW (buyer) → USER_BALANCE (seller) + PLATFORM_FEE
    """
    locked = _lock_order(db, order.id)

    # Idempotent guard — already released
    if locked.status == OrderStatus.COMPLETED:
        logger.info("release_payment called on already COMPLETED order %s — skipping", locked.id)
        return locked

    if locked.status not in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.DISPUTED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal state for payment release: {locked.status}",
        )

    # Handover code check for self-logistics
    from app.models.listing import LogisticsType
    if locked.logistics_type in {LogisticsType.SELF_COLLECT, LogisticsType.SELF_DELIVER}:
        if not verify_handover_code(locked, handover_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Handover Code. Mandatory for Self-Logistics verification.",
            )

    from app.services.wallet_service import WalletService

    idempotency_key = f"escrow_release:{locked.id}"
    success = WalletService.release_escrow(
        db,
        buyer_id=locked.buyer_id,
        seller_id=locked.seller_id,
        amount=locked.total_amount,
        fee=locked.platform_fee,
        currency=locked.currency,
        order_id=locked.id,
        idempotency_key=idempotency_key,
    )
    if not success:
        db.rollback()
        raise HTTPException(status_code=500, detail="Financial Settlement Failed")

    locked.status = OrderStatus.COMPLETED
    locked.completed_at = datetime.now(timezone.utc)

    db.add(Transaction(
        order_id=locked.id, user_id=locked.seller_id,
        type=TransactionType.ESCROW_RELEASE,
        amount=locked.seller_payout, currency=locked.currency, status="completed",
    ))
    db.add(Transaction(
        order_id=locked.id, user_id=locked.buyer_id,
        type=TransactionType.FEE,
        amount=locked.platform_fee, currency=locked.currency, status="completed",
    ))

    db.commit()
    db.refresh(locked)

    # Best-effort post-commit side effects
    _post_release_side_effects(db, locked)
    return locked


def _post_release_side_effects(db: Session, order: Order) -> None:
    """Driver payout, trust score updates, receipt emails — all best-effort."""
    if order.driver_payout and order.driver_payout > 0:
        try:
            from app.models.driver import DriverJob
            from app.services.transport_service import settle_driver_payout
            from sqlalchemy import select as _select
            job = db.execute(
                _select(DriverJob).where(
                    DriverJob.order_id == order.id, DriverJob.status == "DELIVERED"
                )
            ).scalar_one_or_none()
            if job:
                settle_driver_payout(db, job)
        except Exception as exc:
            logger.error("Driver payout failed order=%s: %s", order.id, exc)

    try:
        from app.services.trust_service import update_scores_after_success
        update_scores_after_success(db, order)
    except Exception as exc:
        logger.error("Trust score update failed order=%s: %s", order.id, exc)

    _send_receipt_emails(db, order)


def _send_receipt_emails(db: Session, order: Order) -> None:
    try:
        from app.models.user import User
        from app.services.email_service import email_service

        order_ref = getattr(order, "order_number", None) or str(order.id)
        date_str = ""
        ts = getattr(order, "completed_at", None) or getattr(order, "updated_at", None)
        if ts:
            date_str = ts.strftime("%Y-%m-%d %H:%M")

        for user_id, role_amount in (
            (order.buyer_id, order.total_amount),
            (order.seller_id, getattr(order, "seller_payout", order.total_amount)),
        ):
            user = db.get(User, user_id)
            if not user or not user.email:
                continue
            try:
                email_service.send_template(
                    "email.transaction_receipt",
                    to=user.email,
                    context={
                        "name": user.full_name,
                        "order_ref": order_ref,
                        "amount": f"{role_amount:.2f}",
                        "currency": order.currency,
                        "date": date_str,
                    },
                )
            except Exception as exc:
                logger.warning("Receipt email failed user=%s order=%s: %s", user.id, order.id, exc)
    except Exception as exc:
        logger.warning("Receipt email pipeline error order=%s: %s", order.id, exc)


def refund_payment(db: Session, order: Order) -> Order:
    """
    Transition {ESCROW_HELD | DISPUTED} → REFUNDED.
    Idempotent: already REFUNDED returns the order unchanged.

    Financial flow (via LedgerService, double-entry):
      PENDING_ESCROW (buyer) → USER_BALANCE (buyer)
    """
    locked = _lock_order(db, order.id)

    if locked.status == OrderStatus.REFUNDED:
        logger.info("refund_payment called on already REFUNDED order %s — skipping", locked.id)
        return locked

    if locked.status not in {OrderStatus.ESCROW_HELD, OrderStatus.DISPUTED}:
        raise HTTPException(
            status_code=400,
            detail=f"Refund not allowed in state: {locked.status}",
        )

    from app.services.wallet_service import WalletService

    idempotency_key = f"refund:{locked.id}"
    success = WalletService.refund_escrow(
        db,
        buyer_id=locked.buyer_id,
        amount=locked.total_amount,
        currency=locked.currency,
        idempotency_key=idempotency_key,
    )
    if not success:
        db.rollback()
        raise HTTPException(status_code=500, detail="Refund Transaction Failed")

    locked.status = OrderStatus.REFUNDED
    locked.refunded_at = datetime.now(timezone.utc)

    db.add(Transaction(
        order_id=locked.id, user_id=locked.buyer_id,
        type=TransactionType.REFUND,
        amount=locked.total_amount, currency=locked.currency, status="completed",
    ))

    db.commit()
    db.refresh(locked)
    return locked


def process_auto_settlement(db: Session, order: Order) -> bool:
    """
    Automatic settlement: releases funds after AUTO_SETTLEMENT_DAYS days of
    unchallenged delivery. Enforces real timer — not a simulation.

    Called by the settlement worker on all DELIVERED orders.
    """
    locked = _lock_order(db, order.id)

    if locked.status != OrderStatus.DELIVERED:
        return False

    delivered_at = getattr(locked, "delivered_at", None) or getattr(locked, "updated_at", None)
    if delivered_at is None:
        logger.error("auto_settlement: order %s has no delivered_at timestamp", locked.id)
        return False

    if delivered_at.tzinfo is None:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)

    age = datetime.now(timezone.utc) - delivered_at
    if age < timedelta(days=AUTO_SETTLEMENT_DAYS):
        logger.debug(
            "auto_settlement: order %s not yet eligible (age=%s, required=%d days)",
            locked.id, age, AUTO_SETTLEMENT_DAYS,
        )
        return False

    try:
        release_payment(db, locked)
        logger.info("AUTO_SETTLEMENT order=%s completed after %s", locked.id, age)
        return True
    except Exception as exc:
        logger.error("AUTO_SETTLEMENT failed order=%s: %s", locked.id, exc)
        return False


def resolve_dispute(
    db: Session,
    order: Order,
    buyer_refund: float,
    seller_payout: float,
    fee: float,
) -> Order:
    """
    Transition DISPUTED → SETTLED with a split payout.
    Idempotent: already SETTLED returns the order unchanged.

    Financial flow (via LedgerService):
      PENDING_ESCROW (buyer) → buyer_refund → USER_BALANCE (buyer)
                              → seller_payout → USER_BALANCE (seller)
                              → fee → PLATFORM_FEE
    """
    locked = _lock_order(db, order.id)

    if locked.status == OrderStatus.SETTLED:
        return locked

    if locked.status != OrderStatus.DISPUTED:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be DISPUTED for resolution, current state: {locked.status}",
        )

    total = buyer_refund + seller_payout + fee
    if abs(total - locked.total_amount) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Split amounts ({total}) do not match order total ({locked.total_amount})",
        )

    from app.services.wallet_service import WalletService

    idempotency_key = f"dispute_resolve:{locked.id}"
    success = WalletService.resolve_split(
        db,
        buyer_id=locked.buyer_id,
        seller_id=locked.seller_id,
        total_amount=locked.total_amount,
        buyer_refund=buyer_refund,
        seller_payout=seller_payout,
        currency=locked.currency,
        order_id=locked.id,
        idempotency_key=idempotency_key,
    )
    if not success:
        db.rollback()
        raise HTTPException(status_code=500, detail="Split Settlement Failed")

    locked.status = OrderStatus.SETTLED
    locked.refunded_amount = buyer_refund
    locked.seller_payout = seller_payout
    locked.platform_fee = fee
    locked.settled_at = datetime.now(timezone.utc)

    db.add(Transaction(
        order_id=locked.id, user_id=locked.buyer_id, type=TransactionType.REFUND,
        amount=buyer_refund, currency=locked.currency, status="completed",
    ))
    db.add(Transaction(
        order_id=locked.id, user_id=locked.seller_id, type=TransactionType.ESCROW_RELEASE,
        amount=seller_payout, currency=locked.currency, status="completed",
    ))
    db.add(Transaction(
        order_id=locked.id, user_id=locked.buyer_id, type=TransactionType.FEE,
        amount=fee, currency=locked.currency, status="completed",
    ))

    db.commit()
    db.refresh(locked)
    return locked
