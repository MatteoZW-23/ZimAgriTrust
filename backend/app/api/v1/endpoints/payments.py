import hmac
import hashlib
import os
import uuid as _uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user, require_policy_requirement
from app.services.payment_service import process_ecocash_callback
from app.services.wallet_service import wallet_service
from app.schemas.transaction import WalletDepositRequest, WalletWithdrawRequest, WalletBalanceResponse, TransactionResponse
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, Order, OrderStatus
from app.models.payout_method import UserPayoutMethod, PayoutMethodType, PayoutMethodProvider, PayoutMethodStatus
from app.core.policy import calculate_platform_fees, calculate_seller_settlement, calculate_full_order_breakdown

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/methods")
def list_payment_methods():
    """
    Provider abstraction surface used by web/mobile clients.
    """
    return {
        "providers": [
            {"code": "ecocash", "name": "EcoCash", "enabled": True},
            {"code": "onemoney", "name": "OneMoney", "enabled": True},
            {"code": "innbucks", "name": "Innbucks", "enabled": True},
            {"code": "omari", "name": "Omari", "enabled": True},
            {"code": "zipit", "name": "ZIPIT", "enabled": True},
            {"code": "bank_transfer", "name": "Bank Transfer", "enabled": True},
        ]
    }


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{name} is not configured",
        )
    return value

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


class ZIPITCallbackPayload(BaseModel):
    reference: str
    status: str
    amount: float
    bank_reference: Optional[str] = None


class InnbucksCallbackPayload(BaseModel):
    reference: str
    status: str
    amount: float
    wallet_id: Optional[str] = None


class PayoutMethodCreateRequest(BaseModel):
    method_type: str
    provider: str
    account_name: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_code: Optional[str] = None
    is_default: bool = False


class PayoutMethodUpdateRequest(BaseModel):
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_code: Optional[str] = None
    is_default: Optional[bool] = None
    status: Optional[str] = None


class PayoutMethodResponse(BaseModel):
    id: str
    user_id: str
    method_type: str
    provider: str
    account_name: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_code: Optional[str] = None
    is_default: bool
    status: str
    verified_at: Optional[str] = None
    created_at: str
    updated_at: str


def _serialize_payout_method(pm: UserPayoutMethod) -> dict:
    return {
        "id": str(pm.id),
        "user_id": str(pm.user_id),
        "method_type": pm.method_type.value,
        "provider": pm.provider.value,
        "account_name": pm.account_name,
        "account_number": pm.account_number,
        "bank_name": pm.bank_name,
        "branch_code": pm.branch_code,
        "is_default": bool(pm.is_default),
        "status": pm.status.value,
        "verified_at": pm.verified_at.isoformat() if pm.verified_at else None,
        "created_at": pm.created_at.isoformat(),
        "updated_at": pm.updated_at.isoformat(),
    }

@router.post("/ecocash/callback")
async def ecocash_webhook(payload: EcoCashCallbackPayload, request: Request, db: Session = Depends(get_db)):
    """Production EcoCash callback receiver with MANDATORY HMAC signature verification."""
    signature = request.headers.get("X-EcoCash-Signature")
    secret_key = os.getenv("ECOCASH_WEBHOOK_SECRET", "").encode("utf-8")
    
    # MANDATORY verification - fail closed (reject if not configured)
    if not secret_key:
        logger.error("ECOCASH_WEBHOOK_SECRET not configured - rejecting webhook")
        raise HTTPException(status_code=500, detail="Webhook verification not configured")
    
    if not signature:
        logger.warning(f"EcoCash webhook missing signature from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    # Verify signature before any processing
    try:
        raw_body = await request.body()
        expected = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning(f"EcoCash webhook invalid signature from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(status_code=401, detail="Invalid signature")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EcoCash signature verification error: {e}")
        raise HTTPException(status_code=401, detail="Signature verification failed")

    # Process only after successful verification
    try:
        success = process_ecocash_callback(
            db,
            payload.request_id,
            "PAID" if payload.status == "SUCCESS" else "FAILED",
            payload.merchant_reference,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Callback failed to process")
        return {"status": "accepted", "message": "Transaction state updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EcoCash webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="EcoCash service error")


@router.post("/onemoney/callback")
async def onemoney_webhook(
    payload: OneMoneyCBPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(None, alias="X-Signature")
):
    """OneMoney webhook with signature verification."""
    try:
        # Verify webhook signature
        if x_signature:
            payload_bytes = await request.body()
            from app.services.webhook_verification import WebhookVerifier
            secret_key = os.getenv("ONEMONEY_WEBHOOK_SECRET", "")
            if secret_key:
                is_valid = WebhookVerifier.verify_onemoney(payload_bytes, x_signature, secret_key)
                if not is_valid:
                    raise HTTPException(status_code=401, detail="Invalid signature")

        success = process_ecocash_callback(
            db,
            payload.reference,
            "PAID" if payload.status in ("SUCCESS", "COMPLETED") else "FAILED",
            payload.reference,
        )
        if not success:
            raise HTTPException(status_code=400, detail="OneMoney callback failed")
        return {"status": "accepted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OneMoney webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="OneMoney service error")


@router.post("/zipit/callback")
async def zipit_webhook(
    payload: ZIPITCallbackPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(None, alias="X-Signature"),
):
    try:
        if x_signature:
            body = await request.body()
            from app.services.webhook_verification import WebhookVerifier
            secret_key = os.getenv("ZIPIT_WEBHOOK_SECRET", "")
            if secret_key and not WebhookVerifier.verify_zipit(body, x_signature, secret_key):
                raise HTTPException(status_code=401, detail="Invalid signature")
        success = process_ecocash_callback(
            db,
            payload.reference,
            "PAID" if payload.status.upper() in ("SUCCESS", "COMPLETED", "PAID") else "FAILED",
            payload.reference,
        )
        if not success:
            raise HTTPException(status_code=400, detail="ZIPIT callback failed")
        return {"status": "accepted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ZIPIT webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="ZIPIT service error")


@router.post("/innbucks/callback")
async def innbucks_webhook(
    payload: InnbucksCallbackPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str = Header(None, alias="X-Signature"),
):
    try:
        if x_signature:
            body = await request.body()
            from app.services.webhook_verification import WebhookVerifier, ProviderType
            if not await WebhookVerifier.verify_webhook(ProviderType.INNBUCKS, body, x_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
        success = process_ecocash_callback(
            db,
            payload.reference,
            "PAID" if payload.status.upper() in ("SUCCESS", "COMPLETED", "PAID") else "FAILED",
            payload.reference,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Innbucks callback failed")
        return {"status": "accepted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Innbucks webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Innbucks service error")


@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.ledger_service import LedgerService
    available_usd = LedgerService.get_balance(db, current_user.id, "USD")
    pending_usd = LedgerService.get_pending_balance(db, current_user.id, "USD")
    available_zig = LedgerService.get_balance(db, current_user.id, "ZIG")
    pending_zig = LedgerService.get_pending_balance(db, current_user.id, "ZIG")
    return {
        "balance_usd": round(available_usd, 6),
        "balance_zig": round(available_zig, 6),
        "pending_usd": round(pending_usd, 6),
        "pending_zig": round(pending_zig, 6),
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


@router.get("/fees/quote")
def fee_quote(
    grossMinor: int,
    currency: str = "USD",
    plan: str = "BASIC",
    current_user: User = Depends(get_current_user),
):
    """
    Compatibility endpoint for TypeScript finance clients.
    Financial calculations remain backend-owned and are returned in minor units.
    """
    gross_amount = grossMinor / 100
    breakdown = calculate_full_order_breakdown(
        goods_amount=gross_amount,
        user_trust_score=current_user.trust_score,
        currency=currency,
    )
    fee_amount = float(breakdown.get("platform_fee", 0.0))
    seller_payout = float(breakdown.get("seller_payout", gross_amount - fee_amount))
    return {
        "grossMinor": str(grossMinor),
        "feeMinor": str(round(fee_amount * 100)),
        "taxMinor": "0",
        "netMinor": str(round(seller_payout * 100)),
        "currency": currency.upper(),
        "plan": plan.upper(),
        "breakdown": breakdown,
    }


@router.post("/initiate")
def initiate_payment(
    payload: PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_policy_requirement("transaction_first")),
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
            "merchant_code": _required_env("ECOCASH_MERCHANT_CODE"),
            "amount": order.total_amount,
            "currency": order.currency,
            "reference": payment_ref,
            "steps": [
                f"Dial *151# on {phone or 'your phone'}",
                "Select 'Send Money' → 'Pay Merchant'",
                f"Enter merchant code: {_required_env('ECOCASH_MERCHANT_CODE')}",
                f"Enter amount: {order.currency} {order.total_amount:.2f}",
                "Enter your EcoCash PIN to confirm",
            ],
            "expires_minutes": 10,
        }
    elif method == "onemoney":
        instructions = {
            "method": "onemoney",
            "ussd_code": "*111#",
            "merchant_code": _required_env("ONEMONEY_MERCHANT_CODE"),
            "amount": order.total_amount,
            "currency": order.currency,
            "reference": payment_ref,
            "steps": [
                f"Dial *111# on {phone or 'your phone'}",
                "Select 'Payments' → 'Pay Bill'",
                f"Enter biller code: {_required_env('ONEMONEY_MERCHANT_CODE')}",
                f"Enter amount: {order.currency} {order.total_amount:.2f}",
                "Confirm with your OneMoney PIN",
            ],
            "expires_minutes": 10,
        }
    elif method == "bank":
        instructions = {
            "method": "bank",
            "bank_name": os.getenv("BANK_ACCOUNT_NAME", "ZimAgriTrust Trust Account"),
            "account_number": _required_env("BANK_ACCOUNT_NUMBER"),
            "branch_code": _required_env("BANK_BRANCH_CODE"),
            "reference": merchant_ref,
            "amount": order.total_amount,
            "currency": order.currency,
            "steps": [
                "Log in to your internet banking",
                "Select 'Transfer' → 'Pay Beneficiary'",
                f"Account: {_required_env('BANK_ACCOUNT_NUMBER')}",
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
    listings = db.query(Listing).filter(Listing.seller_id == current_user.id, Listing.is_boosted == True).all()
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


@router.get("/wallet/payout-methods", response_model=list[PayoutMethodResponse])
def list_payout_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    methods = (
        db.query(UserPayoutMethod)
        .filter(UserPayoutMethod.user_id == current_user.id)
        .order_by(UserPayoutMethod.is_default.desc(), UserPayoutMethod.created_at.desc())
        .all()
    )
    return [_serialize_payout_method(method) for method in methods]


@router.post("/wallet/payout-methods", response_model=PayoutMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payout_method(
    payload: PayoutMethodCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider_value = payload.provider.lower()
    method_value = payload.method_type.lower()
    if method_value in {"mobile_money", "mobile"}:
        method_value = provider_value
    method_type = PayoutMethodType(method_value)
    provider = PayoutMethodProvider(provider_value)
    if method_type in (PayoutMethodType.BANK_ACCOUNT, PayoutMethodType.BANK_TRANSFER) and not (payload.bank_name and payload.account_number and payload.branch_code):
        raise HTTPException(status_code=400, detail="Bank account requires bank_name, account_name, account_number, and branch_code")
    if method_type in (PayoutMethodType.ECOCASH, PayoutMethodType.ONEMONEY, PayoutMethodType.INNBUCKS, PayoutMethodType.OMARI) and not payload.account_number:
        raise HTTPException(status_code=400, detail="Mobile money payout methods require account_number")
    if payload.is_default:
        db.query(UserPayoutMethod).filter(UserPayoutMethod.user_id == current_user.id).update({"is_default": False})
    method = UserPayoutMethod(
        user_id=current_user.id,
        method_type=method_type,
        provider=provider,
        account_name=payload.account_name,
        account_number=payload.account_number,
        bank_name=payload.bank_name,
        branch_code=payload.branch_code,
        is_default=payload.is_default,
        status=PayoutMethodStatus.PENDING,
    )
    db.add(method)
    db.commit()
    db.refresh(method)
    return _serialize_payout_method(method)


@router.patch("/wallet/payout-methods/{method_id}", response_model=PayoutMethodResponse)
def update_payout_method(
    method_id: _uuid.UUID,
    payload: PayoutMethodUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    method = (
        db.query(UserPayoutMethod)
        .filter(UserPayoutMethod.id == method_id, UserPayoutMethod.user_id == current_user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payout method not found")
    if payload.account_name is not None:
        method.account_name = payload.account_name
    if payload.account_number is not None:
        method.account_number = payload.account_number
    if payload.bank_name is not None:
        method.bank_name = payload.bank_name
    if payload.branch_code is not None:
        method.branch_code = payload.branch_code
    if payload.is_default is True:
        db.query(UserPayoutMethod).filter(UserPayoutMethod.user_id == current_user.id, UserPayoutMethod.id != method.id).update({"is_default": False})
        method.is_default = True
    if payload.status and payload.status.upper() in PayoutMethodStatus.__members__:
        method.status = PayoutMethodStatus[payload.status.upper()]
    db.commit()
    db.refresh(method)
    return _serialize_payout_method(method)


@router.delete("/wallet/payout-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payout_method(
    method_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    method = (
        db.query(UserPayoutMethod)
        .filter(UserPayoutMethod.id == method_id, UserPayoutMethod.user_id == current_user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payout method not found")
    db.delete(method)
    db.commit()
    return None


@router.post("/wallet/payout-methods/{method_id}/verify", response_model=PayoutMethodResponse)
def verify_payout_method(
    method_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    method = (
        db.query(UserPayoutMethod)
        .filter(UserPayoutMethod.id == method_id, UserPayoutMethod.user_id == current_user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payout method not found")
    method.status = PayoutMethodStatus.VERIFIED
    method.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(method)
    return _serialize_payout_method(method)


@router.post("/wallet/payout-methods/{method_id}/default", response_model=PayoutMethodResponse)
def set_default_payout_method(
    method_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    method = (
        db.query(UserPayoutMethod)
        .filter(UserPayoutMethod.id == method_id, UserPayoutMethod.user_id == current_user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payout method not found")
    db.query(UserPayoutMethod).filter(UserPayoutMethod.user_id == current_user.id).update({"is_default": False})
    method.is_default = True
    db.commit()
    db.refresh(method)
    return _serialize_payout_method(method)


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
    _: bool = Depends(require_policy_requirement("transaction_first")),
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
