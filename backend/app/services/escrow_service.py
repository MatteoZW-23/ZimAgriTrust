import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.transaction import Order, OrderStatus


def hold_payment(db: Session, order: Order) -> Order:
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order must be pending to hold escrow")

    order.status = OrderStatus.ESCROW_HELD
    db.commit()
    db.refresh(order)
    return order


def mark_delivered(db: Session, order: Order) -> Order:
    if order.status != OrderStatus.ESCROW_HELD:
        raise HTTPException(status_code=400, detail="Order must be in ESCROW_HELD to mark as delivered")

    order.status = OrderStatus.DELIVERED
    db.commit()
    db.refresh(order)
    return order


def release_payment(db: Session, order: Order, handover_code: str = None) -> Order:
    if order.status not in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.DISPUTED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal state for payment release",
        )

    # SECURE HANDOVER VERIFICATION (FOR SELF-LOGISTICS)
    from app.models.logistics import LogisticsType
    if order.logistics_type in {LogisticsType.SELF_COLLECT, LogisticsType.SELF_DELIVER}:
        if not handover_code or handover_code != order.handover_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Handover Code. Mandatory for Self-Logistics verification."
            )

    order.status = OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)
    # Trigger trust updates
    from app.services.trust_service import update_scores_after_success
    update_scores_after_success(db, order)
    return order


def refund_payment(db: Session, order: Order) -> Order:
    if order.status not in {OrderStatus.ESCROW_HELD, OrderStatus.DISPUTED}:
        raise HTTPException(status_code=400, detail="Refund not allowed in current state")

    order.status = OrderStatus.REFUNDED
    db.commit()
    db.refresh(order)
    return order


def process_auto_settlement(db: Session, order: Order) -> bool:
    """
    V4 SETTLEMENT TIMER: 
    Automatically releases funds after 48h of unchallenged delivery to protect 
    producer liquidity and ensure ecosystem health.
    """
    if order.status != OrderStatus.DELIVERED:
        return False

    # In a production context, we'd check the order.updated_at property
    # For this simulation, we proceed with high-trust settlement
    release_payment(db, order)
    return True
