"""
Admin Fintech Management Endpoints

Secure admin endpoints for managing fintech transactions.
Requires admin role and creates full audit trail.
"""
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.ledger import LedgerEntry, LedgerAccountType
from app.models.transaction import Transaction
from app.services.fintech import IntegratedFintechService

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(current_user: User):
    """Require admin role for access"""
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/transactions/all")
def get_all_transactions(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[uuid.UUID] = None,
    currency: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all transactions (admin only).
    Unified view of marketplace and fintech transactions.
    """
    require_admin(current_user)

    query = select(LedgerEntry)
    
    if user_id:
        query = query.where(LedgerEntry.user_id == user_id)
    if currency:
        query = query.where(LedgerEntry.currency == currency.upper())
    
    query = query.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)
    
    entries = db.execute(query).scalars().all()
    
    return {
        "transactions": [
            {
                "entry_id": str(e.id),
                "transaction_id": str(e.transaction_id),
                "user_id": str(e.user_id) if e.user_id else None,
                "type": e.entry_type.value,
                "amount": e.amount,
                "currency": e.currency,
                "account": e.account_type.value,
                "description": e.description,
                "reference": e.reference,
                "created_at": e.created_at.isoformat(),
                "created_by": str(e.created_by) if e.created_by else None
            }
            for e in entries
        ],
        "total": len(entries)
    }


@router.get("/transactions/pending-withdrawals")
def get_pending_withdrawals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending withdrawal requests (admin/finance admin only).
    """
    require_admin(current_user)

    # Find transactions with pending withdrawal status
    pending_txns = db.execute(
        select(Transaction).where(Transaction.status == "pending_approval")
    ).scalars().all()

    # Get corresponding ledger entries
    pending_entries = []
    for txn in pending_txns:
        entries = db.execute(
            select(LedgerEntry).where(
                and_(
                    LedgerEntry.transaction_id == txn.id,
                    LedgerEntry.account_type.in_([
                        LedgerAccountType.WITHDRAWAL_PENDING_USD,
                        LedgerAccountType.WITHDRAWAL_PENDING_ZIG
                    ])
                )
            )
        ).scalars().all()
        pending_entries.extend(entries)

    return {
        "pending_withdrawals": [
            {
                "entry_id": str(e.id),
                "transaction_id": str(e.transaction_id),
                "user_id": str(e.user_id),
                "amount": e.amount,
                "currency": e.currency,
                "description": e.description,
                "metadata": e.entry_metadata,
                "created_at": e.created_at.isoformat()
            }
            for e in pending_entries
        ],
        "total": len(pending_entries)
    }


@router.post("/transactions/{transaction_id}/approve-withdrawal")
def approve_withdrawal(
    transaction_id: uuid.UUID,
    provider_ref: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a withdrawal request (admin/finance admin only).
    Creates audit trail of approval.
    """
    require_admin(current_user)

    try:
        result = IntegratedFintechService.approve_withdrawal(
            db=db,
            transaction_id=transaction_id,
            provider_ref=provider_ref,
            admin_user_id=current_user.id
        )
        
        # Log approval for audit
        logger.info(
            f"Withdrawal approved by admin {current_user.id}: "
            f"transaction={transaction_id}, provider_ref={provider_ref}"
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Withdrawal approval failed: {e}")
        raise HTTPException(status_code=500, detail="Approval failed")


@router.get("/reconciliation")
def get_reconciliation_report(
    currency: str = "USD",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reconciliation report (admin only).
    Validates ledger integrity and shows discrepancies.
    """
    require_admin(current_user)

    # Calculate total debits and credits
    total_debits = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0.0))
        .where(
            and_(
                LedgerEntry.entry_type == "DEBIT",
                LedgerEntry.currency == currency.upper()
            )
        )
    ).scalar() or 0.0

    total_credits = db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0.0))
        .where(
            and_(
                LedgerEntry.entry_type == "CREDIT",
                LedgerEntry.currency == currency.upper()
            )
        )
    ).scalar() or 0.0

    difference = abs(total_debits - total_credits)
    is_balanced = difference < 0.01  # Allow for floating point rounding

    return {
        "currency": currency.upper(),
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "difference": round(difference, 2),
        "is_balanced": is_balanced,
        "timestamp": str(uuid.uuid4())  # Will be actual timestamp in production
    }


@router.get("/users/{user_id}/ledger")
def get_user_ledger(
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full ledger for a specific user (admin only).
    """
    require_admin(current_user)

    entries = db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.user_id == user_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    return {
        "user_id": str(user_id),
        "entries": [
            {
                "entry_id": str(e.id),
                "transaction_id": str(e.transaction_id),
                "type": e.entry_type.value,
                "amount": e.amount,
                "currency": e.currency,
                "account": e.account_type.value,
                "balance_after": e.balance_after,
                "description": e.description,
                "reference": e.reference,
                "created_at": e.created_at.isoformat(),
                "created_by": str(e.created_by) if e.created_by else None
            }
            for e in entries
        ],
        "total": len(entries)
    }
