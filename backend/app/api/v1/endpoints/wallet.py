"""
/wallet/* endpoints – unified wallet balance, top-up, withdraw, history.
Thin delegation layer on top of the existing wallet_service and payment_service.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.wallet_service import wallet_service

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class WalletBalanceOut(BaseModel):
    balance: float
    held_in_escrow: float
    available: float
    currency: str = "USD"


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw in USD")
    phone_number: Optional[str] = None  # Override payout phone if needed


class TopUpRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: str = "ecocash"  # ecocash | onemoney | bank
    phone_number: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/balance", response_model=WalletBalanceOut, summary="Get wallet balance")
def get_wallet_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = wallet_service.get_balance_detail(db, current_user.id)
        return WalletBalanceOut(
            balance=data["balance"],
            held_in_escrow=data["held_in_escrow"],
            available=data["available"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/withdraw", summary="Request wallet withdrawal to EcoCash/OneMoney")
def withdraw(
    payload: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = wallet_service.request_withdrawal(
            db,
            user_id=current_user.id,
            amount=payload.amount,
            phone_number=payload.phone_number or current_user.phone_number,
        )
        return {"status": "initiated", "reference": result.get("reference"), "amount": payload.amount}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/top-up", summary="Initiate wallet top-up via EcoCash/OneMoney")
def top_up(
    payload: TopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = wallet_service.initiate_external_payment(
            db,
            user_id=current_user.id,
            amount=payload.amount,
            currency="USD",
            provider=payload.payment_method.upper(),
        )
        return {
            "status": "pending",
            "payment_id": result.get("payment_id"),
            "instruction": result.get("instruction"),
            "provider": result.get("provider"),
            "expires_in_minutes": 30,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history", summary="Get wallet transaction history")
def wallet_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        txns = wallet_service.get_transaction_history(db, current_user.id, limit=limit)
        return [
            {
                "id":         str(t.id),
                "type":       t.type.value if hasattr(t.type, "value") else t.type,
                "amount":     t.amount,
                "currency":   t.currency,
                "status":     t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txns
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary", summary="Wallet summary with earnings breakdown")
def wallet_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = wallet_service.get_summary(db, current_user.id)
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
