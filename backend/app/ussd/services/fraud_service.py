"""USSD Fraud Service."""
from __future__ import annotations
import logging

logger = logging.getLogger("ussd.fraud")

class USSDFraudService:
    @staticmethod
    async def check_transaction_risk(user_id: str, amount: float, phone: str) -> dict:
        return {"risk_level": "low", "score": 0.1, "blocked": False}
    
    @staticmethod
    async def log_suspicious_activity(user_id: str, activity: str, details: dict) -> None:
        logger.warning(f"Suspicious: {activity}", extra={"user_id": user_id, "details": details})

ussd_fraud = USSDFraudService()
