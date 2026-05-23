from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.fintech import IntegratedFintechService
from pydantic import BaseModel, Field


router = APIRouter()


# Schemas
class WalletBalanceResponse(BaseModel):
    user_id: str
    currency: str
    balance: float
    pending_escrow: float
    available: float


class CreditRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    reference: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    idempotency_key: Optional[str] = None


class DebitRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    reference: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None
    idempotency_key: Optional[str] = None


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    provider: str
    idempotency_key: Optional[str] = None


# Wallet endpoints
@router.get("/wallet/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(
    currency: str = "USD",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet balance from secure ledger"""
    return IntegratedFintechService.get_wallet_balance(db, current_user.id, currency)


@router.post("/wallet/credit")
def credit_wallet(
    request: CreditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Credit wallet (e.g., from payment provider)"""
    try:
        return IntegratedFintechService.credit_wallet(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            currency=request.currency,
            reference=request.reference,
            description=request.description,
            metadata=request.metadata,
            idempotency_key=request.idempotency_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallet/debit")
def debit_wallet(
    request: DebitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debit wallet (e.g., for purchase)"""
    try:
        return IntegratedFintechService.debit_wallet(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            currency=request.currency,
            reference=request.reference,
            description=request.description,
            metadata=request.metadata,
            idempotency_key=request.idempotency_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wallet/withdraw")
def request_withdrawal(
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request withdrawal - funds moved to pending until admin approval"""
    try:
        return IntegratedFintechService.request_withdrawal(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            currency=request.currency,
            provider=request.provider,
            idempotency_key=request.idempotency_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/history")
def get_transaction_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history from unified ledger"""
    history = IntegratedFintechService.get_transaction_history(db, current_user.id, limit, offset)
    return {"transactions": history, "total": len(history)}
