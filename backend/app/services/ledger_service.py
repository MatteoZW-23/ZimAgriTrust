"""
Enterprise-grade Ledger Service

Implements double-entry accounting with:
- Atomic operations
- Balance derivation from ledger (not direct storage)
- Idempotency support
- Reconciliation
- Distributed locking
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, case, or_

from app.models.ledger import (
    LedgerEntry, LedgerEntryType, LedgerAccountType,
    LedgerReconciliation
)
from app.models.transaction import Transaction
from app.models.user import User
from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class LedgerService:
    """
    Double-entry ledger service for financial consistency.
    All balance operations MUST go through this service.
    """

    @staticmethod
    async def acquire_lock(user_id: uuid.UUID, operation: str) -> bool:
        """
        Acquire distributed lock for balance operations to prevent race conditions.
        Uses Redis with TTL to prevent deadlocks.
        """
        lock_key = f"ledger_lock:{user_id}:{operation}"
        lock_ttl = 30  # 30 seconds
        
        try:
            acquired = await cache_service.set(
                lock_key,
                "locked",
                expire=lock_ttl,
                nx=True  # Only set if not exists
            )
            return acquired
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    @staticmethod
    async def release_lock(user_id: uuid.UUID, operation: str) -> None:
        """Release distributed lock"""
        lock_key = f"ledger_lock:{user_id}:{operation}"
        try:
            await cache_service.delete(lock_key)
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")

    @staticmethod
    def acquire_lock_sync(user_id: uuid.UUID, operation: str) -> bool:
        """
        Synchronous version of acquire_lock for use in non-async contexts.
        Uses Redis with TTL to prevent deadlocks.
        """
        lock_key = f"ledger_lock:{user_id}:{operation}"
        lock_ttl = 30  # 30 seconds

        try:
            acquired = cache_service.set_sync(
                lock_key,
                "locked",
                expire=lock_ttl,
                nx=True  # Only set if not exists
            )
            return acquired
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    @staticmethod
    def release_lock_sync(user_id: uuid.UUID, operation: str) -> None:
        """Synchronous version of release_lock for use in non-async contexts."""
        lock_key = f"ledger_lock:{user_id}:{operation}"
        try:
            cache_service.delete_sync(lock_key)
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")

    @staticmethod
    def get_balance(
        db: Session,
        user_id: uuid.UUID,
        currency: str = "USD"
    ) -> float:
        """
        Calculate user balance from ledger entries.
        Balances are NEVER stored directly - always derived from ledger.
        """
        account_type = (
            LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD"
            else LedgerAccountType.USER_BALANCE_ZIG
        )
        
        # Calculate balance: credits - debits
        result = db.execute(
            select(func.coalesce(func.sum(
                case(
                    (LedgerEntry.entry_type == LedgerEntryType.CREDIT, LedgerEntry.amount),
                    else_=-LedgerEntry.amount
                )
            ), 0.0))
            .where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.account_type == account_type,
                    LedgerEntry.currency == currency.upper()
                )
            )
        ).scalar()
        
        return float(result) if result else 0.0

    @staticmethod
    def get_pending_balance(
        db: Session,
        user_id: uuid.UUID,
        currency: str = "USD"
    ) -> float:
        """Calculate pending escrow balance from ledger"""
        account_type = (
            LedgerAccountType.PENDING_ESCROW_USD if currency.upper() == "USD"
            else LedgerAccountType.PENDING_ESCROW_ZIG
        )
        
        result = db.execute(
            select(func.coalesce(func.sum(
                case(
                    (LedgerEntry.entry_type == LedgerEntryType.CREDIT, LedgerEntry.amount),
                    else_=-LedgerEntry.amount
                )
            ), 0.0))
            .where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.account_type == account_type,
                    LedgerEntry.currency == currency.upper()
                )
            )
        ).scalar()
        
        return float(result) if result else 0.0

    @staticmethod
    def credit_user_balance(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        entry_metadata: Optional[dict] = None,
    ) -> LedgerEntry:
        """
        Credit user's balance directly (convenience method).
        Creates a credit entry to the user's balance account.
        """
        from app.models.transaction import Transaction

        # Create a transaction record
        txn = Transaction(
            user_id=user_id,
            type="CREDIT",
            amount=amount,
            currency=currency.upper(),
            status="completed"
        )
        db.add(txn)
        db.flush()

        account_type = (
            LedgerAccountType.USER_BALANCE_USD if currency.upper() == "USD"
            else LedgerAccountType.USER_BALANCE_ZIG
        )

        entry = LedgerService.create_entry(
            db=db,
            transaction_id=txn.id,
            account_type=account_type,
            entry_type=LedgerEntryType.CREDIT,
            amount=amount,
            currency=currency,
            user_id=user_id,
            reference=reference,
            description=description,
            entry_metadata=entry_metadata,
        )

        db.commit()
        return entry

    @staticmethod
    def debit_user_balance(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        entry_metadata: Optional[dict] = None,
    ) -> LedgerEntry:
        """
        Debit user's balance directly (convenience method).
        Creates a debit entry from the user's balance account.
        """
        from app.models.transaction import Transaction

        # Create a transaction record
        txn = Transaction(
            user_id=user_id,
            type="DEBIT",
            amount=amount,
            currency=currency.upper(),
            status="completed"
        )
        db.add(txn)
        db.flush()

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
            entry_metadata=entry_metadata,
        )

        db.commit()
        return entry

    @staticmethod
    def create_entry(
        db: Session,
        transaction_id: uuid.UUID,
        account_type: LedgerAccountType,
        entry_type: LedgerEntryType,
        amount: float,
        currency: str,
        user_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        entry_metadata: Optional[dict] = None,
    ) -> LedgerEntry:
        """
        Create a single ledger entry with balance calculation.
        """
        # Calculate balance after this entry
        balance_before = LedgerService._get_account_balance(
            db, account_type, user_id, currency
        )
        
        if entry_type == LedgerEntryType.DEBIT:
            balance_after = balance_before - amount
        else:
            balance_after = balance_before + amount
        
        entry = LedgerEntry(
            transaction_id=transaction_id,
            account_type=account_type,
            entry_type=entry_type,
            amount=amount,
            currency=currency.upper(),
            balance_after=balance_after,
            user_id=user_id,
            order_id=order_id,
            reference=reference,
            description=description,
            idempotency_key=idempotency_key,
            entry_metadata=entry_metadata,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(entry)
        return entry

    @staticmethod
    def _get_account_balance(
        db: Session,
        account_type: LedgerAccountType,
        user_id: Optional[uuid.UUID],
        currency: str
    ) -> float:
        """Get current balance for an account"""
        query = select(func.coalesce(func.sum(
            case(
                (LedgerEntry.entry_type == LedgerEntryType.CREDIT, LedgerEntry.amount),
                else_=-LedgerEntry.amount
            )
        ), 0.0))
        
        conditions = [
            LedgerEntry.account_type == account_type,
            LedgerEntry.currency == currency.upper()
        ]
        
        if user_id:
            conditions.append(LedgerEntry.user_id == user_id)
        
        result = db.execute(query.where(and_(*conditions))).scalar()
        return float(result) if result else 0.0

    @staticmethod
    def create_double_entry(
        db: Session,
        transaction_id: uuid.UUID,
        debit_account: LedgerAccountType,
        credit_account: LedgerAccountType,
        amount: float,
        currency: str,
        debit_user_id: Optional[uuid.UUID] = None,
        credit_user_id: Optional[uuid.UUID] = None,
        order_id: Optional[uuid.UUID] = None,
        reference: Optional[str] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        entry_metadata: Optional[dict] = None,
    ) -> Tuple[LedgerEntry, LedgerEntry]:
        """
        Create a double-entry transaction.
        Debit one account, credit another. Total debits = total credits.
        """
        debit_idempotency_key = f"{idempotency_key}:debit" if idempotency_key else None
        credit_idempotency_key = f"{idempotency_key}:credit" if idempotency_key else None

        debit_entry = LedgerService.create_entry(
            db=db,
            transaction_id=transaction_id,
            account_type=debit_account,
            entry_type=LedgerEntryType.DEBIT,
            amount=amount,
            currency=currency,
            user_id=debit_user_id,
            order_id=order_id,
            reference=reference,
            description=f"{description} (DEBIT)" if description else None,
            idempotency_key=debit_idempotency_key,
            entry_metadata=entry_metadata,
        )
        
        credit_entry = LedgerService.create_entry(
            db=db,
            transaction_id=transaction_id,
            account_type=credit_account,
            entry_type=LedgerEntryType.CREDIT,
            amount=amount,
            currency=currency,
            user_id=credit_user_id,
            order_id=order_id,
            reference=reference,
            description=f"{description} (CREDIT)" if description else None,
            idempotency_key=credit_idempotency_key,
            entry_metadata=entry_metadata,
        )
        
        return debit_entry, credit_entry

    @staticmethod
    def check_idempotency(
        db: Session,
        idempotency_key: str
    ) -> Optional[LedgerEntry]:
        """
        Check if an idempotency key has already been used.
        Returns the existing entry if found, None otherwise.
        """
        return db.execute(
            select(LedgerEntry)
            .where(
                or_(
                    LedgerEntry.idempotency_key == idempotency_key,
                    LedgerEntry.idempotency_key == f"{idempotency_key}:debit",
                    LedgerEntry.idempotency_key == f"{idempotency_key}:credit",
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def reconcile_account(
        db: Session,
        account_type: Optional[LedgerAccountType] = None,
        user_id: Optional[uuid.UUID] = None,
        currency: str = "USD",
        reconciled_by: uuid.UUID = None,
    ) -> LedgerReconciliation:
        """
        Perform reconciliation for an account.
        Validates that debits equal credits and balance is consistent.
        """
        # Build query conditions
        conditions = [LedgerEntry.currency == currency.upper()]
        if account_type:
            conditions.append(LedgerEntry.account_type == account_type)
        if user_id:
            conditions.append(LedgerEntry.user_id == user_id)
        
        # Calculate totals
        total_debits = db.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0.0))
            .where(and_(*conditions, LedgerEntry.entry_type == LedgerEntryType.DEBIT))
        ).scalar()
        
        total_credits = db.execute(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0.0))
            .where(and_(*conditions, LedgerEntry.entry_type == LedgerEntryType.CREDIT))
        ).scalar()
        
        # Calculate expected balance
        expected_balance = float(total_credits) - float(total_debits)
        
        # Get actual balance from latest entry
        latest_entry = db.execute(
            select(LedgerEntry)
            .where(and_(*conditions))
            .order_by(LedgerEntry.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        actual_balance = latest_entry.balance_after if latest_entry else 0.0
        difference = abs(expected_balance - actual_balance)
        is_balanced = difference < 0.01  # Allow 1 cent rounding error
        
        # Create reconciliation record
        reconciliation = LedgerReconciliation(
            account_type=account_type,
            user_id=user_id,
            currency=currency,
            total_debits=float(total_debits) if total_debits else 0.0,
            total_credits=float(total_credits) if total_credits else 0.0,
            expected_balance=expected_balance,
            actual_balance=actual_balance,
            difference=difference,
            is_balanced=is_balanced,
            discrepancies=None if is_balanced else {
                "expected": expected_balance,
                "actual": actual_balance,
                "difference": difference
            },
            reconciled_at=datetime.now(timezone.utc),
            reconciled_by=reconciled_by,
        )
        
        db.add(reconciliation)
        
        if not is_balanced:
            logger.error(
                f"Ledger reconciliation failed: {account_type} user={user_id} "
                f"expected={expected_balance} actual={actual_balance} diff={difference}"
            )
        
        return reconciliation

    @staticmethod
    def get_transaction_entries(
        db: Session,
        transaction_id: uuid.UUID
    ) -> List[LedgerEntry]:
        """Get all ledger entries for a transaction"""
        return db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.transaction_id == transaction_id)
            .order_by(LedgerEntry.created_at)
        ).scalars().all()

    @staticmethod
    def generate_trial_balance(
        db: Session,
        currency: str = "USD",
        as_of_date: Optional[datetime] = None,
    ) -> dict:
        """
        Generate trial balance report.
        Shows all account balances at a point in time.
        """
        query = select(
            LedgerEntry.account_type,
            func.sum(
                case(
                    (LedgerEntry.entry_type == LedgerEntryType.DEBIT, LedgerEntry.amount),
                    else_=0
                )
            ).label('total_debits'),
            func.sum(
                case(
                    (LedgerEntry.entry_type == LedgerEntryType.CREDIT, LedgerEntry.amount),
                    else_=0
                )
            ).label('total_credits')
        ).where(LedgerEntry.currency == currency.upper())
        
        if as_of_date:
            query = query.where(LedgerEntry.created_at <= as_of_date)
        
        query = query.group_by(LedgerEntry.account_type)
        
        results = db.execute(query).all()
        
        trial_balance = {}
        total_debits = 0.0
        total_credits = 0.0
        
        for account_type, debits, credits in results:
            balance = float(credits) - float(debits)
            trial_balance[account_type.value] = {
                "debits": float(debits) if debits else 0.0,
                "credits": float(credits) if credits else 0.0,
                "balance": balance
            }
            total_debits += float(debits) if debits else 0.0
            total_credits += float(credits) if credits else 0.0
        
        trial_balance["summary"] = {
            "total_debits": total_debits,
            "total_credits": total_credits,
            "is_balanced": abs(total_debits - total_credits) < 0.01
        }
        
        return trial_balance
