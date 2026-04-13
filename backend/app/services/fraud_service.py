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


def fake_seller_detected(user: User) -> bool:
    return user.risk_score >= 80 or user.trust_score <= 20
