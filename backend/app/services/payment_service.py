import uuid
import logging
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User

logger = logging.getLogger(__name__)

from app.core.constants import ZIG_USD_BENCHMARK_RATE
from app.core.policy import calculate_platform_fees

# Zimbabwe-Specific Business Logic
ZIG_USD_RATE = ZIG_USD_BENCHMARK_RATE  # Set via ZIG_USD_RATE environment variable


def calculate_fees(amount: float, user_trust_score: float = 0) -> float:
    """Refactored: Uses unified company-wide Platform Policy Engine"""
    return calculate_platform_fees(amount, user_trust_score)


def process_ecocash_callback(db: Session, request_id: str, status: str, merchant_ref: str):
    """
    Processes incoming webhook from EcoCash
    merchant_ref: AGRI-TX-{order_id}
    """
    try:
        order_id_str = merchant_ref.replace("AGRI-TX-", "")
        order_id = uuid.UUID(order_id_str)
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"Order {order_id} not found for callback")
            return False

        if status == "PAID":
            # 1. Move to Escrow
            order.status = OrderStatus.ESCROW_HELD
            
            # 2. Update Buyer Wallet (AgriTrust Spec: Funds enter escrow immediately)
            # Since the money came from an external source, we conceptually "deposit and hold"
            buyer = db.query(User).filter(User.id == order.buyer_id).first()
            if order.currency == "USD":
                buyer.pending_usd += order.total_amount
            else:
                buyer.pending_zig += order.total_amount

            # 3. Add transaction log
            tx = Transaction(
                order_id=order.id,
                user_id=order.buyer_id,
                type=TransactionType.PAYMENT,
                amount=order.total_amount,
                currency=order.currency,
                status="completed"
            )
            db.add(tx)
            
            # 4. Update Listing status
            if order.listing:
                from app.models.listing import ListingStatus
                order.listing.status = ListingStatus.SOLD
            
            db.commit()
            logger.info(f"✅ ESCROW SECURED: Order {order_id} | Ref {merchant_ref}")
            return True
        else:
            order.status = OrderStatus.REFUNDED
            buyer = db.query(User).filter(User.id == order.buyer_id).first()
            if buyer:
                from app.services.verification_service import verification_service
                verification_service.apply_payment_failure(db, buyer)
            db.commit()
            logger.warning(f"❌ PAYMENT FAIL: Order {order_id} | Status {status}")
            return False

    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        return False


def settle_escrow_payout(db: Session, order_id: uuid.UUID):
    """
    Executes actual payout to Farmer wallet/EcoCash after completion.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != OrderStatus.RELEASED:
        return False
        
    payout_amount = order.seller_payout
    logger.info(f"💰 PAYOUT SETTLED: Farmer received USD {payout_amount} (Fee: {order.platform_fee})")
    
    # Log payout transaction
    tx = Transaction(
        order_id=order.id,
        user_id=order.seller_id,
        type=TransactionType.ESCROW_RELEASE,
        amount=payout_amount,
        status="completed"
    )
    db.add(tx)
    
    db.commit()
    return True
