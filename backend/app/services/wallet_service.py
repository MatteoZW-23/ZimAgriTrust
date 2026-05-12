import uuid
import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)

class WalletService:
    @staticmethod
    def deposit(db: Session, user_id: uuid.UUID, amount: float, currency: str, reference: str = None) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        if currency.upper() == "USD":
            user.balance_usd += amount
        elif currency.upper() == "ZIG":
            user.balance_zig += amount
        else:
            return False
            
        txn = Transaction(
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency.upper(),
            status="completed"
        )
        db.add(txn)
        db.commit()
        logger.info(f"Wallet deposit: {amount} {currency} for user {user_id}")
        return True

    @staticmethod
    def withdraw(db: Session, user_id: uuid.UUID, amount: float, currency: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        if currency.upper() == "USD":
            if user.balance_usd < amount:
                return False
            user.balance_usd -= amount
        elif currency.upper() == "ZIG":
            if user.balance_zig < amount:
                return False
            user.balance_zig -= amount
        else:
            return False
            
        txn = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            amount=amount,
            currency=currency.upper(),
            status="completed"
        )
        db.add(txn)
        db.commit()
        logger.info(f"Wallet withdrawal: {amount} {currency} for user {user_id}")
        return True

    @staticmethod
    def hold_escrow(db: Session, user_id: uuid.UUID, amount: float, currency: str) -> bool:
        """Moves funds from available balance to pending (escrow)"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        if currency.upper() == "USD":
            if user.balance_usd < amount:
                return False
            user.balance_usd -= amount
            user.pending_usd += amount
        elif currency.upper() == "ZIG":
            if user.balance_zig < amount:
                return False
            user.balance_zig -= amount
            user.pending_zig += amount
        else:
            return False
            
        db.commit()
        return True

    @staticmethod
    def release_escrow(db: Session, buyer_id: uuid.UUID, seller_id: uuid.UUID, amount: float, fee: float, currency: str) -> bool:
        """Releases funds from buyer's pending to seller's available balance minus fee"""
        buyer = db.query(User).filter(User.id == buyer_id).first()
        seller = db.query(User).filter(User.id == seller_id).first()
        
        if not buyer or not seller:
            return False
            
        payout = amount - fee
        
        if currency.upper() == "USD":
            if buyer.pending_usd < amount:
                return False
            buyer.pending_usd -= amount
            seller.balance_usd += payout
        elif currency.upper() == "ZIG":
            if buyer.pending_zig < amount:
                return False
            buyer.pending_zig -= amount
            seller.balance_zig += payout
        else:
            return False
            
        db.commit()
        return True

    @staticmethod
    def refund_escrow(db: Session, buyer_id: uuid.UUID, amount: float, currency: str) -> bool:
        """Returns pending funds back to buyer's available balance"""
        buyer = db.query(User).filter(User.id == buyer_id).first()
        if not buyer:
            return False
            
        if currency.upper() == "USD":
            if buyer.pending_usd < amount:
                return False
            buyer.pending_usd -= amount
            buyer.balance_usd += amount
        elif currency.upper() == "ZIG":
            if buyer.pending_zig < amount:
                return False
            buyer.pending_zig -= amount
            buyer.balance_zig += amount
        else:
            return False
            
        db.commit()
        return True

    @staticmethod
    def resolve_split(db: Session, buyer_id: uuid.UUID, seller_id: uuid.UUID, total_amount: float, buyer_refund: float, seller_payout: float, currency: str) -> bool:
        """Resolves a dispute by splitting pending funds between buyer and seller."""
        buyer = db.query(User).filter(User.id == buyer_id).first()
        seller = db.query(User).filter(User.id == seller_id).first()
        
        if not buyer or not seller:
            return False
            
        if currency.upper() == "USD":
            if buyer.pending_usd < total_amount:
                return False
            buyer.pending_usd -= total_amount
            buyer.balance_usd += buyer_refund
            seller.balance_usd += seller_payout
        elif currency.upper() == "ZIG":
            if buyer.pending_zig < total_amount:
                return False
            buyer.pending_zig -= total_amount
            buyer.balance_zig += buyer_refund
            seller.balance_zig += seller_payout
        else:
            return False
            
        db.commit()
        return True

    @staticmethod
    def initiate_external_payment(db: Session, user_id: uuid.UUID, amount: float, currency: str, provider: str = "EcoCash") -> dict:
        """
        Simulates integration with Zimbabwean payment gateways (EcoCash, OneMoney, Banks).
        """
        # In a real system, this would call an external API (e.g., Paynow, Pesepay)
        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        logger.info(f"Initiated {provider} payment of {amount} {currency} for user {user_id}. Ref: {payment_id}")
        
        return {
            "status": "pending",
            "payment_id": payment_id,
            "provider": provider,
            "instruction": "Please check your phone for a USSD prompt to authorize the transaction."
        }

    @staticmethod
    def confirm_external_payment(db: Session, payment_id: str) -> bool:
        """
        Webhook verification of payment — implement real provider callback logic here.
        """
        # Real logic: check a 'Payment' table or call provider API
        logger.info(f"External payment {payment_id} — awaiting real provider confirmation.")
        return False

    @staticmethod
    def get_balance(db: Session, user_id: uuid.UUID) -> float:
        user = db.query(User).filter(User.id == user_id).first()
        return user.balance_usd if user else 0.0

    @staticmethod
    def get_balance_detail(db: Session, user_id: uuid.UUID) -> dict:
        """Returns full wallet balance breakdown as a dict."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"balance": 0.0, "held_in_escrow": 0.0, "available": 0.0}
        held = user.pending_usd
        bal  = user.balance_usd
        return {
            "balance":       round(bal + held, 2),
            "held_in_escrow": round(held, 2),
            "available":     round(bal, 2),
        }

    @staticmethod
    def request_withdrawal(db: Session, user_id: uuid.UUID, amount: float, phone_number: str) -> dict:
        """Initiates a withdrawal to EcoCash/OneMoney phone number."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        if user.balance_usd < amount:
            raise ValueError(f"Insufficient balance. Available: ${user.balance_usd:.2f}")
        if amount < 1.0:
            raise ValueError("Minimum withdrawal is $1.00")

        reference = f"WD-{uuid.uuid4().hex[:10].upper()}"
        user.balance_usd -= amount
        txn = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            amount=amount,
            currency="USD",
            status="pending",
        )
        db.add(txn)
        db.commit()
        logger.info(f"Withdrawal requested: {amount} USD for user {user_id} → {phone_number}. Ref: {reference}")
        return {"reference": reference, "amount": amount, "phone_number": phone_number, "status": "pending"}

    @staticmethod
    def get_summary(db: Session, user_id: uuid.UUID) -> dict:
        """Returns wallet summary with lifetime earnings, spending, and current balance."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        from sqlalchemy import func as sa_func
        from app.models.transaction import TransactionType as TT

        def _sum(tx_type: str) -> float:
            result = (
                db.query(sa_func.coalesce(sa_func.sum(Transaction.amount), 0.0))
                .filter(Transaction.user_id == user_id, Transaction.type == tx_type, Transaction.status == "completed")
                .scalar()
            )
            return float(result or 0.0)

        total_deposited  = _sum(TT.DEPOSIT)
        total_withdrawn  = _sum(TT.WITHDRAWAL)
        total_received   = _sum(TT.ESCROW_RELEASE)
        total_spent      = _sum(TT.ESCROW_HOLD)

        return {
            "balance":            round(user.balance_usd, 2),
            "held_in_escrow":     round(user.pending_usd, 2),
            "available":          round(user.balance_usd, 2),
            "currency":           "USD",
            "total_deposited":    round(total_deposited, 2),
            "total_withdrawn":    round(total_withdrawn, 2),
            "total_received":     round(total_received, 2),
            "total_spent":        round(total_spent, 2),
            "trust_score":        user.trust_score,
            "subscription_tier":  user.subscription_tier.value if user.subscription_tier else "basic",
        }

    @staticmethod
    def get_transaction_history(db: Session, user_id: uuid.UUID, limit: int = 10) -> list[Transaction]:
        return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).limit(limit).all()

wallet_service = WalletService()
