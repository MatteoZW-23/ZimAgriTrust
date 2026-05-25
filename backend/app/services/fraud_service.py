from sqlalchemy.orm import Session
from app.models.user import User
from app.core.constants import RISK_THRESHOLD_SUSPEND, RISK_THRESHOLD_MODERATE


def apply_listing_controls(_: Session, user: User) -> User:
    """
    Automated Governance: Adjusts listing capacity based on real-time risk scores.
    """
    if user.risk_score >= RISK_THRESHOLD_SUSPEND:
        user.is_suspended = True
        user.listing_limit = 0
    elif user.risk_score >= RISK_THRESHOLD_MODERATE:
        user.listing_limit = 2
    else:
        user.listing_limit = 10
    return user


def is_high_risk_seller(user: User) -> bool:
    return user.risk_score >= 80 or user.trust_score <= 20


def check_transaction_risk(amount: float, currency: str, user: User) -> bool:
    """
    ZimAgritrust Spec: Fraud Detection & Security
    Flag suspicious transactions for manual review.
    """
    # 1. High-Value Transaction Threshold
    if currency == "USD" and amount > 500:
        return True # Requires 2FA/Manual Review
        
    # 2. Account Risk State
    if user.is_suspended or user.risk_score > 70:
        return True
        
    return False
