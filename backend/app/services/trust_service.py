import uuid
from sqlalchemy.orm import Session
from app.models.dispute import Dispute
from app.models.listing import Listing
from app.models.transaction import Order, OrderStatus
from app.models.user import User


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

    user.trust_score = clamp_score(50 + successful_orders * 8 - disputes * 12 - failed_orders * 10)
    
    # Also update predictive risk
    from app.services.risk_service import evaluate_user_risk
    evaluate_user_risk(user)
    
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

    farmer.trust_score = clamp_score(45 + sold_count * 10 - disputes * 10 + min(listings_count, 10))
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
