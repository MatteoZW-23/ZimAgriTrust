import uuid
from sqlalchemy.orm import Session
from app.models.dispute import Dispute
from app.models.listing import Listing, Offer, OfferStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User
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
    
    # We look for orders that were cancelled without a corresponding dispute
    cancelled_orders = db.query(Order).filter(
        (Order.buyer_id == user.id) | (Order.seller_id == user.id),
        Order.status == OrderStatus.CANCELLED
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


def recompute_user_scores(db: Session, user: User) -> User:
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
    user.trust_score = clamp_score(50 + successful_orders * 8 - disputes * 12 - failed_orders * 10 - leakage_penalty)
    
    # Also update predictive risk
    from app.services.risk_service import evaluate_user_risk
    evaluate_user_risk(db, user)
    
    db.commit()
    db.refresh(user)
    return user


def update_farmer_scores(db: Session, farmer: User) -> User:
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
    farmer.trust_score = clamp_score(45 + sold_count * 10 - disputes * 10 + min(listings_count, 10) - leakage_penalty)
    db.commit()
    db.refresh(farmer)
    return farmer


def update_scores_after_success(db: Session, order: Order) -> None:
    recompute_user_scores(db, order.buyer)
    update_farmer_scores(db, order.seller)


def update_scores_after_dispute(
    db: Session, order: Order, release_to_farmer: bool
) -> None:
    if release_to_farmer:
        order.buyer.trust_score = clamp_score(order.buyer.trust_score - 8)
    else:
        order.seller.trust_score = clamp_score(order.seller.trust_score - 10)

    db.commit()
