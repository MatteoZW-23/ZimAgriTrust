"""USSD Wallet Service."""
from __future__ import annotations
from typing import Any, Optional

class USSDWalletService:
    @staticmethod
    async def get_balance(db: Any, user_id: str) -> float:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        return user.wallet_balance_usd if user else 0.0
    
    @staticmethod
    async def get_transactions(db: Any, user_id: str, limit: int = 5) -> List[Any]:
        from app.models.transaction import Transaction
        return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).limit(limit).all()

ussd_wallet = USSDWalletService()
