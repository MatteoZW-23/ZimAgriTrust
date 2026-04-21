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
    def get_balance(db: Session, user_id: uuid.UUID) -> float:
        user = db.query(User).filter(User.id == user_id).first()
        return user.balance_usd if user else 0.0

wallet_service = WalletService()
