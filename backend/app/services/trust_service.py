import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.dispute import Dispute
from app.models.listing import Listing, Offer, OfferStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User, UserRole, TrustScoreEvent
import logging

logger = logging.getLogger(__name__)


def detect_leakage_risk(db: Session, user: User) -> float:
    """
    HEURISTIC: Detects 'Platform Leakage' patterns.
    High ratio of cancelled offers after acceptance suggests off-platform settlement.
    """
    total_accepted = db.query(Offer).filter(
        (Offer.buyer_id == user.id) | (Offer.seller_id == user.id),
        Offer.status == OfferStatus.ACCEPTED
    ).count()
    
    # We look for orders that were refunded without a corresponding dispute
    # (REFUNDED is the closest proxy for a cancelled/abandoned order in this system)
    cancelled_orders = db.query(Order).filter(
        (Order.buyer_id == user.id) | (Order.seller_id == user.id),
        Order.status == OrderStatus.REFUNDED
    ).count()
    
    if total_accepted == 0: return 0.0
    
    leakage_ratio = cancelled_orders / total_accepted
    if leakage_ratio > 0.3: # Over 30% cancellation rate is highly suspicious
        penalty = leakage_ratio * 25 # Major penalty for potential leakage
        logger.warning(f"LEAKAGE_DETECTED | User {user.id} has suspicious cancellation ratio: {leakage_ratio}")
        return penalty
    return 0.0



def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def _record_trust_event(db: Session, user: User, delta: int, reason: str, triggered_by: str = "system") -> None:
    """Record a trust score change event in the audit log."""
    previous = user.trust_score
    new_score = max(0, min(100, previous + delta))
    user.trust_score = new_score
    
    event = TrustScoreEvent(
        user_id=user.id,
        previous_score=previous,
        new_score=new_score,
        delta=delta,
        reason=reason,
        triggered_by=triggered_by,
    )
    db.add(event)
    db.commit()
    db.refresh(user)
    logger.info(f"Trust score update: user={user.id}, {previous} -> {new_score} ({delta:+d}) reason={reason}")


def recompute_user_scores(db: Session, user: User) -> User:
    """Recompute buyer trust score from base + history."""
    from app.services.verification_service import verification_service
    
    # Start from verification-based initial score
    base_score = verification_service.get_initial_trust(user)
    
    successful_orders = (
        db.query(Order)
        .filter(Order.buyer_id == user.id, Order.status == OrderStatus.COMPLETED)
        .count()
    )
    disputes = (
        db.query(Dispute)
        .join(Order, Dispute.order_id == Order.id)
        .filter(Order.buyer_id == user.id)
        .count()
    )
    failed_orders = (
        db.query(Order)
        .filter(Order.buyer_id == user.id, Order.status == OrderStatus.REFUNDED)
        .count()
    )

    leakage_penalty = detect_leakage_risk(db, user)
    
    # Use new comprehensive formula for buyers
    buyer_scores = verification_service.TRUST_SCORES.get(UserRole.BUYER, {})
    score = base_score
    score += successful_orders * buyer_scores.get("successful_purchase", 2)
    score += (successful_orders // 5) * buyer_scores.get("milestone_5_transactions", 0)
    score -= disputes * 12
    score -= failed_orders * 10
    score -= leakage_penalty
    
    user.trust_score = clamp_score(score)
    
    # Also update predictive risk
    from app.services.risk_service import evaluate_user_risk
    evaluate_user_risk(db, user)
    
    db.commit()
    db.refresh(user)
    return user


def update_farmer_scores(db: Session, farmer: User) -> User:
    """Recompute farmer trust score from base + history."""
    from app.services.verification_service import verification_service
    
    base_score = verification_service.get_initial_trust(farmer)
    
    listings_count = db.query(Listing).filter(Listing.seller_id == farmer.id).count()
    sold_count = (
        db.query(Order)
        .filter(Order.seller_id == farmer.id, Order.status == OrderStatus.COMPLETED)
        .count()
    )
    disputes = (
        db.query(Dispute)
        .join(Order, Dispute.order_id == Order.id)
        .filter(Order.seller_id == farmer.id)
        .count()
    )

    leakage_penalty = detect_leakage_risk(db, farmer)
    
    farmer_scores = verification_service.TRUST_SCORES.get(UserRole.FARMER, {})
    score = base_score
    score += sold_count * farmer_scores.get("successful_transaction", 2)
    score += (sold_count // 5) * farmer_scores.get("milestone_5_transactions", 10)
    score -= disputes * 10
    score += min(listings_count, 5)
    score -= leakage_penalty
    
    farmer.trust_score = clamp_score(score)
    db.commit()
    db.refresh(farmer)
    return farmer


def update_agent_scores(db: Session, agent: User) -> User:
    """Recompute agent trust score from base + performance."""
    from app.services.verification_service import verification_service
    
    base_score = verification_service.get_initial_trust(agent)
    
    # Get agent profile verification count
    verification_count = 0
    if agent.agent_profile:
        verification_count = agent.agent_profile.verification_count or 0
    
    agent_scores = verification_service.TRUST_SCORES.get(UserRole.AGENT, {})
    score = base_score
    score += (verification_count // 10) * agent_scores.get("accurate_verification_10", 1)
    
    agent.trust_score = clamp_score(score)
    db.commit()
    db.refresh(agent)
    return agent


def update_scores_after_success(db: Session, order: Order) -> None:
    recompute_user_scores(db, order.buyer)
    update_farmer_scores(db, order.seller)
    
    # Check for first transaction milestone
    buyer_completed = db.query(Order).filter(
        Order.buyer_id == order.buyer_id,
        Order.status == OrderStatus.COMPLETED
    ).count()
    if buyer_completed == 1:
        from app.services.verification_service import verification_service
        verification_service.record_first_transaction(db, order.buyer)
    
    seller_completed = db.query(Order).filter(
        Order.seller_id == order.seller_id,
        Order.status == OrderStatus.COMPLETED
    ).count()
    if seller_completed == 1:
        from app.services.verification_service import verification_service
        verification_service.record_first_transaction(db, order.seller)


def update_scores_after_dispute(
    db: Session, order: Order, release_to_farmer: bool
) -> None:
    from app.services.verification_service import verification_service
    losing_user = order.buyer if release_to_farmer else order.seller
    verification_service.apply_dispute_penalty(db, losing_user, ruled_against=True)


def check_and_apply_inactivity(db: Session, user: User) -> bool:
    """Check if user has been inactive and apply penalty if needed."""
    if not user.last_activity_at:
        return False
    
    days_inactive = (datetime.utcnow() - user.last_activity_at).days
    
    if days_inactive >= 60 and user.role == UserRole.FARMER:
        _record_trust_event(db, user, -10, "Inactivity penalty (60 days)", triggered_by="system")
        return True
    elif days_inactive >= 30:
        _record_trust_event(db, user, -5, "Inactivity penalty (30 days)", triggered_by="system")
        return True
    
    return False


class TrustService:
    @staticmethod
    def detect_leakage_risk(db: Session, user: User) -> float:
        return detect_leakage_risk(db, user)

    @staticmethod
    def recompute_user_scores(db: Session, user: User) -> User:
        return recompute_user_scores(db, user)

    @staticmethod
    def update_farmer_scores(db: Session, farmer: User) -> User:
        return update_farmer_scores(db, farmer)

    @staticmethod
    def update_agent_scores(db: Session, agent: User) -> User:
        return update_agent_scores(db, agent)

    @staticmethod
    def update_scores_after_success(db: Session, order: Order) -> None:
        return update_scores_after_success(db, order)

    @staticmethod
    def update_scores_after_dispute(db: Session, order: Order, release_to_farmer: bool) -> None:
        return update_scores_after_dispute(db, order, release_to_farmer)
    
    @staticmethod
    def check_and_apply_inactivity(db: Session, user: User) -> bool:
        return check_and_apply_inactivity(db, user)

trust_core = TrustService()
