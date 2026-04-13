from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.payment_service import process_ecocash_callback
from pydantic import BaseModel

router = APIRouter()

class EcoCashCallbackPayload(BaseModel):
    request_id: str
    status: str # SUCCESS, PENDING, FAILED
    merchant_reference: str # Our prefixed transaction ID
    amount: float

@router.post("/ecocash/callback")
async def ecocash_webhook(payload: EcoCashCallbackPayload, db: Session = Depends(get_db)):
    """
    Simulated EcoCash callback receiver.
    In production, this would use HMAC/Secret signature verification.
    """
    success = process_ecocash_callback(
        db, 
        payload.request_id, 
        "PAID" if payload.status == "SUCCESS" else "FAILED", 
        payload.merchant_reference
    )
    if not success:
        raise HTTPException(status_code=400, detail="Callback failed to process")
        
    return {"status": "accepted", "message": "Transaction state updated"}


@router.get("/simulate-payment/{tx_id}")
async def simulate_payment_start(tx_id: int):
    """
    Helper to simulate the start of a payment (as if from USSD or Mobile App).
    """
    return {
        "tx_id": tx_id,
        "instructions": "Dial *151# on your EcoCash phone",
        "mock_pay_link": f"http://localhost:8080/api/v1/payments/simulate-success/{tx_id}"
    }

from app.api.deps import get_db, get_current_user
from app.models.user import User

@router.get("/simulate-success/{tx_id}")
async def simulate_success(tx_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fast simulation helper for testing.
    """
    success = process_ecocash_callback(db, "MOCK-REQ-123", "PAID", f"AGRI-TX-{tx_id}")
    return {"status": "success" if success else "failed"}
