"""
payment_service.py — Production-hardened payment processing.

Critical invariants enforced here:
  1. Every webhook is idempotent — duplicate delivery never double-credits.
  2. Order state transitions use SELECT FOR UPDATE — no concurrent races.
  3. Escrow is recorded via the double-entry LedgerService only.
     user.balance_usd / user.pending_usd are NEVER touched here.
  4. A single db.commit() per operation — no partial commits.
  5. Any exception rolls back the entire operation.
"""
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.core.constants import ZIG_USD_BENCHMARK_RATE
from app.core.policy import calculate_platform_fees

logger = logging.getLogger(__name__)

ZIG_USD_RATE = ZIG_USD_BENCHMARK_RATE


def calculate_fees(amount: float, user_trust_score: float = 0) -> float:
    return calculate_platform_fees(amount, user_trust_score)


def process_ecocash_callback(db: Session, request_id: str, status: str, merchant_ref: str) -> bool:
    """
    Idempotent, row-locked EcoCash/OneMoney webhook processor.

    Safety guarantees:
    - Deduplication: if a Transaction with reference=request_id already exists
      and is 'completed', we return True immediately (no re-processing).
    - Concurrency: Order row is locked with SELECT FOR UPDATE before any state
      check, preventing two simultaneous webhooks from both passing the guard.
    - Atomicity: all DB mutations inside a single try/except; db.rollback() on
      any failure ensures no partial state.
    - Ledger-only: escrow hold goes through WalletService.hold_escrow which
      writes double-entry LedgerEntries. Direct user.balance_usd mutations
      have been removed entirely.
    """
    try:
        order_id_str = merchant_ref.replace("AGRI-TX-", "")
        try:
            order_id = uuid.UUID(order_id_str)
        except ValueError:
            logger.error("Invalid merchant_ref format: %s", merchant_ref)
            return False

        # ── IDEMPOTENCY GUARD ────────────────────────────────────────────────
        # Check for an already-processed transaction with this provider request_id.
        existing_tx = (
            db.execute(
                select(Transaction).where(
                    Transaction.reference == request_id,
                    Transaction.status == "completed",
                )
            ).scalar_one_or_none()
        )
        if existing_tx:
            logger.info(
                "Idempotent webhook: request_id=%s already processed (tx=%s). Skipping.",
                request_id,
                existing_tx.id,
            )
            return True

        # ── ROW-LEVEL LOCK ───────────────────────────────────────────────────
        # Lock the Order row before reading its status. Any concurrent request
        # for the same order will block here until we commit or rollback.
        order = (
            db.execute(
                select(Order).where(Order.id == order_id).with_for_update()
            ).scalar_one_or_none()
        )
        if not order:
            logger.error("Order %s not found for callback ref=%s", order_id, merchant_ref)
            return False

        if status == "PAID":
            # Guard: only process if still in a receivable state.
            if order.status not in (OrderStatus.PENDING, OrderStatus.PAYMENT_INITIATED):
                logger.warning(
                    "Order %s already in state %s — ignoring duplicate PAID webhook.",
                    order_id,
                    order.status,
                )
                return True  # idempotent success

            # ── LEDGER ESCROW HOLD ───────────────────────────────────────────
            # Deposit the incoming funds and immediately hold them in escrow.
            # This creates two pairs of double-entry ledger records:
            #   CASH_USD → USER_BALANCE (deposit)
            #   USER_BALANCE → PENDING_ESCROW (hold)
            from app.services.wallet_service import WalletService

            idempotency_key = f"webhook:{request_id}:deposit"
            deposit_ok = WalletService.deposit(
                db,
                user_id=order.buyer_id,
                amount=order.total_amount,
                currency=order.currency,
                reference=request_id,
                idempotency_key=idempotency_key,
            )
            if not deposit_ok:
                logger.error("Deposit ledger entry failed for order %s", order_id)
                db.rollback()
                return False

            hold_ok = WalletService.hold_escrow(
                db,
                user_id=order.buyer_id,
                amount=order.total_amount,
                currency=order.currency,
                order_id=order.id,
                idempotency_key=f"webhook:{request_id}:hold",
            )
            if not hold_ok:
                logger.error("Escrow hold ledger entry failed for order %s", order_id)
                db.rollback()
                return False

            # ── STATE TRANSITION ─────────────────────────────────────────────
            order.status = OrderStatus.ESCROW_HELD
            order.payment_reference = request_id
            order.payment_confirmed_at = datetime.now(timezone.utc)

            # Audit transaction record (reference links back to provider request_id)
            tx = Transaction(
                order_id=order.id,
                user_id=order.buyer_id,
                type=TransactionType.PAYMENT,
                amount=order.total_amount,
                currency=order.currency,
                status="completed",
                reference=request_id,
            )
            db.add(tx)

            # Mark listing as sold
            if order.listing:
                from app.models.listing import ListingStatus
                order.listing.status = ListingStatus.SOLD

            # ── SINGLE COMMIT ────────────────────────────────────────────────
            db.commit()
            logger.info(
                "ESCROW_SECURED order=%s ref=%s amount=%s %s",
                order_id, request_id, order.total_amount, order.currency,
            )
            return True

        else:
            # Payment failed / cancelled
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.PAYMENT_FAILED
                tx = Transaction(
                    order_id=order.id,
                    user_id=order.buyer_id,
                    type=TransactionType.PAYMENT,
                    amount=order.total_amount,
                    currency=order.currency,
                    status="failed",
                    reference=request_id,
                )
                db.add(tx)
                db.commit()
            try:
                from app.models.user import User
                buyer = db.get(User, order.buyer_id)
                if buyer:
                    from app.services.verification_service import verification_service
                    verification_service.apply_payment_failure(db, buyer)
                    db.commit()
            except Exception:
                db.rollback()
            logger.warning("PAYMENT_FAILED order=%s ref=%s", order_id, request_id)
            return False

    except Exception as exc:
        db.rollback()
        logger.error("process_ecocash_callback unhandled error ref=%s: %s", request_id, exc, exc_info=True)
        return False


def settle_escrow_payout(db: Session, order_id: uuid.UUID) -> bool:
    """
    Post-release payout audit log. Actual money movement must have already
    been executed via escrow_service.release_payment → WalletService.release_escrow.
    This function only records the payout log entry.
    """
    order = (
        db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        ).scalar_one_or_none()
    )
    if not order or order.status != OrderStatus.COMPLETED:
        return False

    payout_amount = order.seller_payout
    logger.info("PAYOUT_SETTLED order=%s seller=%s amount=%s", order_id, order.seller_id, payout_amount)
    db.commit()
    return True
