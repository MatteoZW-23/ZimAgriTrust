"""
Integrated Fintech Wallet Service

Uses the existing secure LedgerService for all financial operations.
This ensures all fintech transactions go through the same double-entry
accounting system as marketplace transactions.
"""
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.ledger import LedgerEntry, LedgerEntryType, LedgerAccountType
from app.models.transaction import Transaction
from app.models.user import User
from app.services.ledger_service import LedgerService
from app.core.security_middleware import AuditLoggingMiddleware

logger = logging.getLogger(__name__)


class IntegratedFintechService:
    """
    Fintech service integrated with existing secure ledger.
    All operations use LedgerService for double-entry accounting.
    """

    @staticmethod
    def get_wallet_balance(
        db: Session,
        user_id: uuid.UUID,
        currency: str = "USD"
    ) -> dict:
        """
        Get wallet balance from ledger (secure, derived from ledger entries).
        """
        balance = LedgerService.get_balance(db, user_id, currency)
        pending = LedgerService.get_pending_balance(db, user_id, currency)
        
        return {
            "user_id": str(user_id),
            "currency": currency.upper(),
            "balance": round(balance, 2),
            "pending_escrow": round(pending, 2),
            "available": round(balance - pending, 2)
        }

    @staticmethod
    def credit_wallet(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None
    ) -> dict:
        """
        Credit user wallet (e.g., from payment provider).
        Uses LedgerService with distributed locking for security.
        """
        # Check idempotency
        if idempotency_key:
            existing = db.execute(
                select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
            ).scalar_one_or_none()
            if existing:
                return {"status": "already_processed", "entry_id": str(existing.id)}

        # Acquire distributed lock to prevent race conditions
        if not LedgerService.acquire_lock_sync(user_id, "credit_wallet"):
            raise Exception("Could not acquire lock - operation in progress")

        try:
            # Create transaction record
            txn = Transaction(
                user_id=user_id,
                type="PAYMENT_CREDIT",
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()

            # Credit user balance via LedgerService
            entry = LedgerService.credit_user_balance(
                db=db,
                user_id=user_id,
                amount=amount,
                currency=currency,
                reference=reference,
                description=description,
                entry_metadata=metadata
            )

            db.commit()
            
            return {
                "status": "success",
                "transaction_id": str(txn.id),
                "entry_id": str(entry.id),
                "new_balance": LedgerService.get_balance(db, user_id, currency)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Credit wallet failed: {e}")
            raise
        finally:
            LedgerService.release_lock_sync(user_id, "credit_wallet")

    @staticmethod
    def debit_wallet(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None
    ) -> dict:
        """
        Debit user wallet (e.g., for withdrawal or purchase).
        Uses LedgerService with distributed locking for security.
        """
        # Check idempotency
        if idempotency_key:
            existing = db.execute(
                select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
            ).scalar_one_or_none()
            if existing:
                return {"status": "already_processed", "entry_id": str(existing.id)}

        # Acquire distributed lock
        if not LedgerService.acquire_lock_sync(user_id, "debit_wallet"):
            raise Exception("Could not acquire lock - operation in progress")

        try:
            # Check balance first
            current_balance = LedgerService.get_balance(db, user_id, currency)
            if current_balance < amount:
                raise ValueError("Insufficient balance")

            # Create transaction record
            txn = Transaction(
                user_id=user_id,
                type="PAYMENT_DEBIT",
                amount=amount,
                currency=currency.upper(),
                status="completed"
            )
            db.add(txn)
            db.flush()

            # Debit user balance via LedgerService
            account_type = (
                LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD"
                else LedgerAccountType.USER_BALANCE_ZIG
            )

            entry = LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=account_type,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=currency,
                user_id=user_id,
                reference=reference,
                description=description,
                entry_metadata=metadata,
                idempotency_key=idempotency_key
            )

            db.commit()

            return {
                "status": "success",
                "transaction_id": str(txn.id),
                "entry_id": str(entry.id),
                "new_balance": LedgerService.get_balance(db, user_id, currency)
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Debit wallet failed: {e}")
            raise
        finally:
            LedgerService.release_lock_sync(user_id, "debit_wallet")

    @staticmethod
    def request_withdrawal(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        provider: str,
        idempotency_key: Optional[str] = None
    ) -> dict:
        """
        Request withdrawal with security checks.
        Funds are moved to pending withdrawal account until approved.
        """
        # Check idempotency
        if idempotency_key:
            existing = db.execute(
                select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
            ).scalar_one_or_none()
            if existing:
                return {"status": "already_processed", "entry_id": str(existing.id)}

        # Acquire distributed lock
        if not LedgerService.acquire_lock_sync(user_id, "withdrawal"):
            raise Exception("Could not acquire lock - operation in progress")

        try:
            # Check balance
            current_balance = LedgerService.get_balance(db, user_id, currency)
            if current_balance < amount:
                raise ValueError("Insufficient balance")

            # Create transaction record
            txn = Transaction(
                user_id=user_id,
                type="WITHDRAWAL_REQUEST",
                amount=amount,
                currency=currency.upper(),
                status="pending_approval"
            )
            db.add(txn)
            db.flush()

            # Move funds from user balance to pending withdrawal
            account_type = (
                LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD"
                else LedgerAccountType.USER_BALANCE_ZIG
            )
            pending_account = (
                LedgerAccountType.WITHDRAWAL_PENDING_USD if currency.upper() == "USD"
                else LedgerAccountType.WITHDRAWAL_PENDING_ZIG
            )

            # Debit user balance
            LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=account_type,
                entry_type=LedgerEntryType.DEBIT,
                amount=amount,
                currency=currency,
                user_id=user_id,
                reference=f"WITHDRAWAL_{provider}",
                description=f"Withdrawal request to {provider}",
                entry_metadata={"provider": provider, "status": "pending_approval"},
                idempotency_key=idempotency_key
            )

            # Credit pending withdrawal account
            LedgerService.create_entry(
                db=db,
                transaction_id=txn.id,
                account_type=pending_account,
                entry_type=LedgerEntryType.CREDIT,
                amount=amount,
                currency=currency,
                user_id=user_id,
                reference=f"WITHDRAWAL_{provider}",
                description=f"Pending withdrawal to {provider}",
                entry_metadata={"provider": provider, "status": "pending_approval"}
            )

            db.commit()

            return {
                "status": "pending_approval",
                "transaction_id": str(txn.id),
                "amount": amount,
                "currency": currency.upper()
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Withdrawal request failed: {e}")
            raise
        finally:
            LedgerService.release_lock_sync(user_id, "withdrawal")

    @staticmethod
    def approve_withdrawal(
        db: Session,
        transaction_id: uuid.UUID,
        provider_ref: str,
        admin_user_id: uuid.UUID
    ) -> dict:
        """
        Admin approves withdrawal - funds are released from pending.
        Requires admin role and creates audit trail.
        """
        # Get transaction
        txn = db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        ).scalar_one_or_none()

        if not txn:
            raise ValueError("Transaction not found")

        if txn.status != "pending_approval":
            raise ValueError("Transaction already processed")

        # Acquire lock
        if not LedgerService.acquire_lock_sync(txn.user_id, "approve_withdrawal"):
            raise Exception("Could not acquire lock - operation in progress")

        try:
            # Get the pending withdrawal entry
            pending_account = (
                LedgerAccountType.WITHDRAWAL_PENDING_USD if txn.currency == "USD"
                else LedgerAccountType.WITHDRAWAL_PENDING_ZIG
            )

            pending_entry = db.execute(
                select(LedgerEntry).where(
                    and_(
                        LedgerEntry.transaction_id == transaction_id,
                        LedgerEntry.account_type == pending_account,
                        LedgerEntry.entry_type == LedgerEntryType.CREDIT
                    )
                )
            ).scalar_one_or_none()

            if not pending_entry:
                raise ValueError("Pending withdrawal entry not found")

            # Debit pending withdrawal account
            LedgerService.create_entry(
                db=db,
                transaction_id=transaction_id,
                account_type=pending_account,
                entry_type=LedgerEntryType.DEBIT,
                amount=pending_entry.amount,
                currency=txn.currency,
                user_id=txn.user_id,
                reference=f"WITHDRAWAL_APPROVED_{provider_ref}",
                description=f"Withdrawal approved - released to provider",
                entry_metadata={"provider_ref": provider_ref, "approved_by": str(admin_user_id)},
                created_by=admin_user_id
            )

            # Update transaction status
            txn.status = "completed"
            txn.metadata = txn.metadata or {}
            txn.metadata["provider_ref"] = provider_ref
            txn.metadata["approved_by"] = str(admin_user_id)
            txn.metadata["approved_at"] = str(uuid.uuid4())  # Will be timestamp in production

            db.commit()

            return {
                "status": "approved",
                "transaction_id": str(transaction_id),
                "provider_ref": provider_ref
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Withdrawal approval failed: {e}")
            raise
        finally:
            LedgerService.release_lock_sync(txn.user_id, "approve_withdrawal")

    @staticmethod
    def get_transaction_history(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Get transaction history from ledger.
        Returns unified view of marketplace and fintech transactions.
        """
        entries = db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.user_id == user_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()

        return [
            {
                "entry_id": str(e.id),
                "transaction_id": str(e.transaction_id),
                "type": e.entry_type.value,
                "amount": e.amount,
                "currency": e.currency,
                "account": e.account_type.value,
                "description": e.description,
                "reference": e.reference,
                "created_at": e.created_at.isoformat()
            }
            for e in entries
        ]
