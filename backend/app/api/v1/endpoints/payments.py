import hmac
import hashlib
import os
import uuid as _uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.services.payment_service import process_ecocash_callback
from app.services.wallet_service import wallet_service
from app.schemas.transaction import WalletDepositRequest, WalletWithdrawRequest, WalletBalanceResponse, TransactionResponse
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, Order, OrderStatus
from app.core.policy import calculate_platform_fees, calculate_seller_settlement, calculate_full_order_breakdown

router = APIRouter()

class EcoCashCallbackPayload(BaseModel):
    request_id: str
    status: str # SUCCESS, PENDING, FAILED
    merchant_reference: str # Our prefixed transaction ID
    amount: float


class PaymentInitiateRequest(BaseModel):
    order_id: str
    payment_method: str = "ecocash"  # ecocash, onemoney, bank, cash_agent
    phone_number: Optional[str] = None


class FeePreviewRequest(BaseModel):
    amount: float
    currency: str = "USD"
    using_platform_transport: bool = False
    transport_fee: float = 0.0
    transport_insurance_elected: bool = False


class OneMoneyCBPayload(BaseModel):
    reference: str
    status: str
    amount: float
    mobile_number: str

@router.post("/ecocash/callback")
async def ecocash_webhook(payload: EcoCashCallbackPayload, request: Request, db: Session = Depends(get_db)):
    """Production EcoCash callback receiver with HMAC signature verification."""
    signature = request.headers.get("X-EcoCash-Signature")
    secret_key = os.getenv("ECOCASH_WEBHOOK_SECRET", "").encode("utf-8")
    if secret_key and signature:
        raw_body = await request.body()
        expected = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    success = process_ecocash_callback(
        db,
        payload.request_id,
        "PAID" if payload.status == "SUCCESS" else "FAILED",
        payload.merchant_reference,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Callback failed to process")
    return {"status": "accepted", "message": "Transaction state updated"}


@router.post("/onemoney/callback")
async def onemoney_webhook(payload: OneMoneyCBPayload, request: Request, db: Session = Depends(get_db)):
    """OneMoney webhook — same escrow logic as EcoCash."""
    success = process_ecocash_callback(
        db,
        payload.reference,
        "PAID" if payload.status in ("SUCCESS", "COMPLETED") else "FAILED",
        payload.reference,
    )
    if not success:
        raise HTTPException(status_code=400, detail="OneMoney callback failed")
    return {"status": "accepted"}


@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(current_user: User = Depends(get_current_user)):
    return {
        "balance_usd": current_user.balance_usd,
        "balance_zig": current_user.balance_zig,
        "pending_usd": current_user.pending_usd,
        "pending_zig": current_user.pending_zig,
    }


@router.get("/fee-preview")
def fee_preview(
    amount: float,
    currency: str = "USD",
    using_platform_transport: bool = False,
    transport_fee: float = 0.0,
    transport_insurance_elected: bool = False,
    current_user: User = Depends(get_current_user),
):
    """
    Full fee breakdown before buyer commits to payment.
    Shows on-platform transport savings and optional insurance fee.
    """
    return calculate_full_order_breakdown(
        goods_amount=amount,
        user_trust_score=current_user.trust_score,
        currency=currency,
        using_platform_transport=using_platform_transport,
        transport_fee=transport_fee,
        transport_insurance_elected=transport_insurance_elected,
    )


@router.post("/initiate")
def initiate_payment(
    payload: PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiates payment for an existing order.
    Returns USSD instructions or payment link depending on method.
    """
    try:
        order_id = _uuid.UUID(payload.order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Order is already {order.status.value}")

    method = payload.payment_method.lower()
    phone = payload.phone_number or current_user.phone_number or ""
    merchant_ref = f"AGRI-TX-{order.id}"
    payment_ref = f"PAY-{_uuid.uuid4().hex[:8].upper()}"

    # Build method-specific instructions
    if method == "ecocash":
        instructions = {
            "method": "ecocash",
            "ussd_code": "*151#",
            "merchant_code": os.getenv("ECOCASH_MERCHANT_CODE", "123456"),
            "amount": order.total_amount,
            "currency": order.currency,
            "reference": payment_ref,
            "steps": [
                f"Dial *151# on {phone or 'your phone'}",
                "Select 'Send Money' → 'Pay Merchant'",
                f"Enter merchant code: {os.getenv('ECOCASH_MERCHANT_CODE', '123456')}",
                f"Enter amount: {order.currency} {order.total_amount:.2f}",
                "Enter your EcoCash PIN to confirm",
            ],
            "expires_minutes": 10,
        }
    elif method == "onemoney":
        instructions = {
            "method": "onemoney",
            "ussd_code": "*111#",
            "merchant_code": os.getenv("ONEMONEY_MERCHANT_CODE", "654321"),
            "amount": order.total_amount,
            "currency": order.currency,
            "reference": payment_ref,
            "steps": [
                f"Dial *111# on {phone or 'your phone'}",
                "Select 'Payments' → 'Pay Bill'",
                f"Enter biller code: {os.getenv('ONEMONEY_MERCHANT_CODE', '654321')}",
                f"Enter amount: {order.currency} {order.total_amount:.2f}",
                "Confirm with your OneMoney PIN",
            ],
            "expires_minutes": 10,
        }
    elif method == "bank":
        instructions = {
            "method": "bank",
            "bank_name": "ZimAgritrust Trust Account — CBZ Bank",
            "account_number": os.getenv("BANK_ACCOUNT_NUMBER", "1234567890"),
            "branch_code": os.getenv("BANK_BRANCH_CODE", "001"),
            "reference": merchant_ref,
            "amount": order.total_amount,
            "currency": order.currency,
            "steps": [
                "Log in to your internet banking",
                "Select 'Transfer' → 'Pay Beneficiary'",
                f"Account: {os.getenv('BANK_ACCOUNT_NUMBER', '1234567890')}",
                f"Reference: {merchant_ref}",
                f"Amount: {order.currency} {order.total_amount:.2f}",
                "Allow 1-2 business days for processing",
            ],
            "expires_minutes": 1440,  # 24 hours
        }
    else:  # cash_agent
        instructions = {
            "method": "cash_agent",
            "reference": payment_ref,
            "amount": order.total_amount,
            "currency": order.currency,
            "steps": [
                "Visit your nearest ZimAgritrust agent",
                f"Provide reference: {payment_ref}",
                f"Pay: {order.currency} {order.total_amount:.2f} in cash",
                "Agent will confirm payment on the platform",
            ],
            "expires_minutes": 1440,
        }

    # For demo/dev: auto-confirm small payments immediately
    auto_confirm = os.getenv("AUTO_CONFIRM_PAYMENTS", "true").lower() == "true"
    if auto_confirm and order.total_amount <= 500:
        process_ecocash_callback(db, payment_ref, "PAID", merchant_ref)
        return {
            "status": "confirmed",
            "payment_ref": payment_ref,
            "order_id": str(order.id),
            "order_number": order.order_number,
            "amount": order.total_amount,
            "currency": order.currency,
            "message": "Payment confirmed. Funds held in escrow.",
            "instructions": instructions,
        }

    return {
        "status": "pending",
        "payment_ref": payment_ref,
        "order_id": str(order.id),
        "order_number": order.order_number,
        "amount": order.total_amount,
        "currency": order.currency,
        "message": "Follow the instructions to complete payment.",
        "instructions": instructions,
    }


@router.get("/status/{payment_ref}")
def get_payment_status(
    payment_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll payment status by payment reference."""
    # Find the most recent transaction matching this reference
    txn = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .first()
    )
    if not txn:
        return {"status": "pending", "payment_ref": payment_ref}
    return {
        "status": txn.status,
        "payment_ref": payment_ref,
        "amount": txn.amount,
        "currency": txn.currency,
        "type": txn.type.value,
        "created_at": txn.created_at.isoformat(),
    }


@router.post("/refund/{order_id}")
def refund_order(
    order_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Refund an order that is in ESCROW_HELD or DISPUTED state."""
    from app.models.user import UserRole
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only buyer or admin can request refund
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.services.escrow_service import refund_payment
    updated = refund_payment(db, order)
    return {
        "status": "refunded",
        "order_id": str(updated.id),
        "order_number": updated.order_number,
        "amount": updated.total_amount,
        "currency": updated.currency,
        "message": "Funds have been returned to your wallet.",
    }


@router.get("/earnings")
def get_seller_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns earnings summary for the current user (seller or farmer).
    Includes total sales, fees paid, and net payout.
    """
    from app.models.transaction import OrderStatus

    # Sales as seller
    orders = db.query(Order).filter(
        Order.seller_id == current_user.id,
        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED])
    ).all()

    total_sales = sum(o.total_amount for o in orders)
    total_fees = sum(o.platform_fee for o in orders)
    total_payout = sum(o.seller_payout for o in orders)

    # Transport commissions earned by this user as driver/agent proxy
    transport_earned = sum(
        o.transport_commission for o in orders if o.transport_commission
    )

    # Boost fees paid by this user (as listing owner)
    from app.models.listing import Listing
    listings = db.query(Listing).filter(Listing.farmer_id == current_user.id, Listing.is_boosted == True).all()
    boost_fees_paid = sum(l.boost_fee or 0.0 for l in listings)

    # Wallet transactions summary
    deposits = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.DEPOSIT
    ).scalar() or 0.0

    withdrawals = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == TransactionType.WITHDRAWAL
    ).scalar() or 0.0

    return {
        "total_sales": round(total_sales, 2),
        "total_fees": round(total_fees, 2),
        "net_payout": round(total_payout, 2),
        "transport_commission": round(transport_earned, 2),
        "boost_fees_paid": round(boost_fees_paid, 2),
        "total_deposits": round(deposits, 2),
        "total_withdrawals": round(withdrawals, 2),
        "order_count": len(orders),
        "listing_count": len(listings),
        "currency": "USD",
    }


@router.get("/wallet/transactions", response_model=List[TransactionResponse])
def get_wallet_transactions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full transaction history for the current user's wallet."""
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/deposit", response_model=TransactionResponse)
def initiate_deposit(
    payload: WalletDepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Wallet deposit — initiates EcoCash/bank payment prompt."""
    txn = Transaction(
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    # Auto-confirm small deposits in dev mode
    auto_confirm = os.getenv("AUTO_CONFIRM_PAYMENTS", "true").lower() == "true"
    if auto_confirm and payload.amount <= 1000:
        wallet_service.deposit(db, current_user.id, payload.amount, payload.currency, str(txn.id))
        txn.status = "completed"
        db.commit()
        db.refresh(txn)

    return txn


@router.get("/withdraw/quote")
def withdraw_quote(
    amount: float,
    currency: str = "USD",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pre-flight quote: returns fee, net, tier, and remaining caps.
    Does NOT debit any funds. Use to display the breakdown to the user.
    """
    from app.services.withdrawal_limits_service import check_withdrawal
    return check_withdrawal(db, user=current_user, amount=amount, currency=currency)


@router.post("/withdraw", response_model=TransactionResponse)
def initiate_withdrawal(
    payload: WalletWithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cash-secured wallet withdrawal.

    Pipeline:
      1. Pre-flight tier limits + fee + min + 3/day cap (`check_withdrawal`).
      2. Fraud detection (velocity / structuring / new-user / duplicate-bank).
      3. HMAC sign the intended transaction (signature + nonce stored).
      4. Execute fund movement via `wallet_service.withdraw`.
      5. Append to tamper-proof audit chain.
    """
    from app.services.withdrawal_limits_service import check_withdrawal
    from app.services.fraud_detection_service import evaluate_withdrawal
    from app.services.transaction_signing_service import sign_transaction, verify_signature
    from app.services.audit_chain_service import append_audit
    from app.models.security import FraudSeverity

    quote = check_withdrawal(db, user=current_user, amount=payload.amount, currency=payload.currency)

    alerts = evaluate_withdrawal(db, user=current_user, amount=payload.amount)
    blocking = [a for a in alerts if a.severity in (FraudSeverity.HIGH, FraudSeverity.CRITICAL)]
    if blocking:
        db.commit()  # persist alerts + notifications
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FRAUD_REVIEW_REQUIRED",
                "message": "Withdrawal flagged for manual review",
                "alerts": [a.alert_type.value for a in blocking],
            },
        )

    signature, signed_payload = sign_transaction(
        user_id=str(current_user.id),
        txn_type=TransactionType.WITHDRAWAL.value,
        amount=quote["amount"],
        currency=quote["currency"],
        extra={"fee": quote["fee"], "net": quote["net"], "tier": quote["tier"]},
    )
    if not verify_signature(signed_payload, signature):
        raise HTTPException(status_code=500, detail="Signing self-check failed")

    success = wallet_service.withdraw(db, current_user.id, payload.amount, payload.currency)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient funds or invalid currency")

    txn = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id, Transaction.type == TransactionType.WITHDRAWAL)
        .order_by(Transaction.created_at.desc())
        .first()
    )

    append_audit(
        db,
        table_name="transactions",
        record_id=str(txn.id) if txn else "unknown",
        operation="WITHDRAWAL",
        payload={
            "user_id": str(current_user.id),
            "amount": quote["amount"],
            "fee": quote["fee"],
            "net": quote["net"],
            "currency": quote["currency"],
            "tier": quote["tier"],
            "signature": signature,
            "signed_payload": signed_payload,
        },
        actor_id=str(current_user.id),
        actor_role=current_user.role.value,
    )
    db.commit()

    # Notifications: SMS to user + email to admin (best-effort)
    try:
        from app.services.sms_service import sms_service
        if current_user.phone_number:
            sms_service.send_sms(  # type: ignore[attr-defined]
                current_user.phone_number,
                f"[ZimAgriTrust] Withdrawal of ${quote['amount']:.2f} (fee ${quote['fee']:.2f}, "
                f"net ${quote['net']:.2f}) processed.",
            )
    except Exception:
        pass

    return txn
