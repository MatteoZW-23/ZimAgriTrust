import hmac
import hashlib
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.services.payment_service import process_ecocash_callback
from app.services.wallet_service import wallet_service
from app.schemas.transaction import WalletDepositRequest, WalletWithdrawRequest, WalletBalanceResponse, TransactionResponse
from app.models.user import User

router = APIRouter()

class EcoCashCallbackPayload(BaseModel):
    request_id: str
    status: str # SUCCESS, PENDING, FAILED
    merchant_reference: str # Our prefixed transaction ID
    amount: float

@router.post("/ecocash/callback")
async def ecocash_webhook(payload: EcoCashCallbackPayload, request: Request, db: Session = Depends(get_db)):
    """
    Production EcoCash callback receiver with HMAC signature verification.
    """
    # 1. Verify Request Signature
    signature = request.headers.get("X-EcoCash-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Signature missing")
        
    secret_key = os.getenv("ECOCASH_WEBHOOK_SECRET", "").encode('utf-8')
    if secret_key:
        raw_body = await request.body()
        expected = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Process callback safely
    success = process_ecocash_callback(
        db, 
        payload.request_id, 
        "PAID" if payload.status == "SUCCESS" else "FAILED", 
        payload.merchant_reference
    )
    if not success:
        raise HTTPException(status_code=400, detail="Callback failed to process")
        
    return {"status": "accepted", "message": "Transaction state updated_securely"}

@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(current_user: User = Depends(get_current_user)):
    return {
        "balance_usd": current_user.balance_usd,
        "balance_zig": current_user.balance_zig,
        "pending_usd": current_user.pending_usd,
        "pending_zig": current_user.pending_zig
    }


@router.post("/deposit", response_model=TransactionResponse)
def initiate_deposit(
    payload: WalletDepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AgriTrust Spec: Wallet Deposit Flow.
    Initiates payment prompt (EcoCash/Bank).
    """
    from app.models.transaction import Transaction, TransactionType
    txn = Transaction(
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=payload.amount,
        currency=payload.currency,
        status="pending"
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    
    # Simulate the Automated Callback Triggering
    if payload.payment_method == "ecocash" and payload.amount < 1000: # Fast track small deposits
        process_ecocash_callback(db, str(txn.id), "PAID", f"AGRI-DEP-{txn.id}")

    return txn


@router.post("/withdraw", response_model=TransactionResponse)
def initiate_withdrawal(
    payload: WalletWithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AgriTrust Spec: Wallet Withdrawal Flow.
    Checks balance and initiates transfer.
    """
    from app.models.transaction import Transaction
    success = wallet_service.withdraw(db, current_user.id, payload.amount, payload.currency)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid currency")

    return db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "WITHDRAWAL" # Match based on type
    ).order_by(Transaction.created_at.desc()).first()
