"""
ZimAgritrust Delivery Service
Full 9-state lifecycle: PENDING_PICKUP → AUTO_CONFIRMED
Handles method selection, status transitions, notifications, and auto-confirm.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.logistics import DeliveryMethod, DeliveryStatus, OrderDelivery
from app.models.transaction import Order, OrderStatus

logger = logging.getLogger(__name__)

# Buyer has this many hours to confirm or dispute after delivery
INSPECTION_WINDOW_HOURS = 24


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_delivery(db: Session, order_id: uuid.UUID) -> OrderDelivery:
    d = db.query(OrderDelivery).filter(OrderDelivery.order_id == order_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery record not found for this order")
    return d


def _get_order(db: Session, order_id: uuid.UUID) -> Order:
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return o


def _transition(delivery: OrderDelivery, new_status: DeliveryStatus, db: Session) -> None:
    delivery.status = new_status
    delivery.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(delivery)


# ── Public API ─────────────────────────────────────────────────────────────────

def create_delivery_record(db: Session, order: Order) -> OrderDelivery:
    """
    Called immediately after an offer is accepted and escrow is funded.
    Creates the delivery tracking record in PENDING_PICKUP state.
    """
    existing = db.query(OrderDelivery).filter(OrderDelivery.order_id == order.id).first()
    if existing:
        return existing

    delivery = OrderDelivery(order_id=order.id)
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    logger.info("Delivery record created for order %s", order.id)
    return delivery


def set_delivery_method(
    db: Session,
    order_id: uuid.UUID,
    method: DeliveryMethod,
    pickup_address: Optional[str] = None,
    delivery_address: Optional[str] = None,
    pickup_scheduled_at: Optional[datetime] = None,
) -> OrderDelivery:
    """Step 2 — Delivery method selection."""
    delivery = _get_delivery(db, order_id)
    if delivery.status != DeliveryStatus.PENDING_PICKUP:
        raise HTTPException(status_code=400, detail="Delivery method already set")

    delivery.method = method
    delivery.pickup_address = pickup_address
    delivery.delivery_address = delivery_address
    delivery.pickup_scheduled_at = pickup_scheduled_at
    _transition(delivery, DeliveryStatus.PICKUP_SCHEDULED, db)

    _notify_method_confirmed(db, order_id, method)
    return delivery


def assign_agent(db: Session, order_id: uuid.UUID, agent_id: uuid.UUID) -> OrderDelivery:
    """Assign a field agent to witness pickup/delivery."""
    delivery = _get_delivery(db, order_id)
    delivery.agent_id = agent_id
    db.commit()
    db.refresh(delivery)
    _notify_agent_assigned(db, order_id, agent_id)
    return delivery


def assign_driver(
    db: Session,
    order_id: uuid.UUID,
    driver_id: Optional[uuid.UUID],
    driver_name: Optional[str],
    vehicle_reg: Optional[str],
) -> OrderDelivery:
    """Assign a third-party driver."""
    delivery = _get_delivery(db, order_id)
    delivery.driver_id = driver_id
    delivery.driver_name = driver_name
    delivery.vehicle_reg = vehicle_reg
    db.commit()
    db.refresh(delivery)
    _notify_driver_assigned(db, order_id)
    return delivery


def mark_pickup_in_progress(db: Session, order_id: uuid.UUID) -> OrderDelivery:
    """Step 3 — Agent/driver en route to farm."""
    delivery = _get_delivery(db, order_id)
    _transition(delivery, DeliveryStatus.PICKUP_IN_PROGRESS, db)
    _notify_pickup_in_progress(db, order_id)
    return delivery


def confirm_pickup(
    db: Session,
    order_id: uuid.UUID,
    photos: Optional[list] = None,
    gps_verified: bool = False,
    estimated_arrival_at: Optional[datetime] = None,
) -> OrderDelivery:
    """Step 3 complete — Goods collected, now in transit."""
    delivery = _get_delivery(db, order_id)
    if delivery.status not in (DeliveryStatus.PICKUP_IN_PROGRESS, DeliveryStatus.PICKUP_SCHEDULED):
        raise HTTPException(status_code=400, detail=f"Cannot confirm pickup from state {delivery.status}")

    delivery.pickup_photos = photos or []
    delivery.pickup_gps_verified = gps_verified
    delivery.estimated_arrival_at = estimated_arrival_at
    _transition(delivery, DeliveryStatus.PICKUP_COMPLETED, db)

    # Immediately move to IN_TRANSIT
    _transition(delivery, DeliveryStatus.IN_TRANSIT, db)
    _notify_pickup_completed(db, order_id, estimated_arrival_at)
    return delivery


def mark_delayed(db: Session, order_id: uuid.UUID, new_eta: Optional[datetime] = None) -> OrderDelivery:
    """Mark delivery as delayed with updated ETA."""
    delivery = _get_delivery(db, order_id)
    delivery.estimated_arrival_at = new_eta
    _transition(delivery, DeliveryStatus.DELAYED, db)
    _notify_delay(db, order_id, new_eta)
    return delivery


def mark_arrived(db: Session, order_id: uuid.UUID) -> OrderDelivery:
    """Step 5 — Driver/goods arrived at buyer location."""
    delivery = _get_delivery(db, order_id)
    _transition(delivery, DeliveryStatus.ARRIVED, db)
    _notify_arrival(db, order_id)
    return delivery


def confirm_delivery(
    db: Session,
    order_id: uuid.UUID,
    photos: Optional[list] = None,
    gps_verified: bool = False,
) -> OrderDelivery:
    """Step 5 complete — Agent confirms goods handed over. Starts inspection window."""
    delivery = _get_delivery(db, order_id)
    if delivery.status not in (DeliveryStatus.ARRIVED, DeliveryStatus.IN_TRANSIT, DeliveryStatus.DELIVERY_IN_PROGRESS):
        raise HTTPException(status_code=400, detail=f"Cannot confirm delivery from state {delivery.status}")

    delivery.delivery_photos = photos or []
    delivery.delivery_gps_verified = gps_verified
    delivery.delivered_at = datetime.now(timezone.utc)
    delivery.inspection_deadline = datetime.now(timezone.utc) + timedelta(hours=INSPECTION_WINDOW_HOURS)

    # Update order status to DELIVERED
    order = _get_order(db, order_id)
    order.status = OrderStatus.DELIVERED
    db.commit()

    _transition(delivery, DeliveryStatus.DELIVERED, db)
    _notify_delivery_completed(db, order_id, delivery.inspection_deadline)
    return delivery


def buyer_confirm_receipt(db: Session, order_id: uuid.UUID, buyer_id: uuid.UUID) -> OrderDelivery:
    """
    Step 6 — Buyer confirms receipt. Triggers escrow release.
    """
    delivery = _get_delivery(db, order_id)
    order = _get_order(db, order_id)

    if order.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="Only the buyer can confirm receipt")

    if delivery.status != DeliveryStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Delivery not yet completed")

    delivery.confirmed_at = datetime.now(timezone.utc)
    _transition(delivery, DeliveryStatus.CONFIRMED, db)

    # Release escrow
    from app.services.escrow_service import release_payment
    release_payment(db, order)

    _notify_buyer_confirmed(db, order_id)
    return delivery


def auto_confirm_expired(db: Session) -> int:
    """
    Scheduler job — auto-confirm all deliveries past their inspection deadline.
    Returns count of orders auto-confirmed.
    """
    now = datetime.now(timezone.utc)
    expired = (
        db.query(OrderDelivery)
        .filter(
            OrderDelivery.status == DeliveryStatus.DELIVERED,
            OrderDelivery.inspection_deadline <= now,
        )
        .all()
    )

    count = 0
    for delivery in expired:
        try:
            order = _get_order(db, delivery.order_id)
            delivery.confirmed_at = now
            _transition(delivery, DeliveryStatus.AUTO_CONFIRMED, db)
            from app.services.escrow_service import release_payment
            release_payment(db, order)
            _notify_auto_confirmed(db, delivery.order_id)
            count += 1
        except Exception as e:
            logger.error("Auto-confirm failed for order %s: %s", delivery.order_id, e)

    if count:
        logger.info("Auto-confirmed %d deliveries", count)
    return count


def get_delivery(db: Session, order_id: uuid.UUID) -> OrderDelivery:
    return _get_delivery(db, order_id)


# ── Notification helpers ───────────────────────────────────────────────────────

def _get_parties(db: Session, order_id: uuid.UUID):
    """Returns (farmer_phone, buyer_phone) for an order."""
    order = _get_order(db, order_id)
    farmer_phone = order.seller.phone_number if order.seller else None
    buyer_phone  = order.buyer.phone_number  if order.buyer  else None
    return farmer_phone, buyer_phone, order


def _sms(phone: Optional[str], msg: str):
    if not phone:
        return
    try:
        from app.services.sms_service import _send_sms
        _send_sms(phone, msg)
    except Exception as e:
        logger.warning("SMS failed to %s: %s", phone, e)


def _notify_method_confirmed(db: Session, order_id: uuid.UUID, method: DeliveryMethod):
    farmer, buyer, order = _get_parties(db, order_id)
    msg = f"ZimAgritrust Order #{order.order_number}: Delivery method confirmed ({method.value.replace('_', ' ')}). Arrange within 48 hours."
    _sms(farmer, msg)
    _sms(buyer, msg)


def _notify_agent_assigned(db: Session, order_id: uuid.UUID, agent_id: uuid.UUID):
    from app.models.user import User
    agent = db.query(User).filter(User.id == agent_id).first()
    agent_name = agent.full_name if agent else "An agent"
    farmer, buyer, order = _get_parties(db, order_id)
    msg = f"ZimAgritrust Order #{order.order_number}: {agent_name} has been assigned to witness your delivery."
    _sms(farmer, msg)
    _sms(buyer, msg)
    if agent:
        _sms(agent.phone_number, f"ZimAgritrust: You have been assigned to Order #{order.order_number}. Check your dashboard.")


def _notify_driver_assigned(db: Session, order_id: uuid.UUID):
    farmer, buyer, order = _get_parties(db, order_id)
    delivery = _get_delivery(db, order_id)
    msg = f"ZimAgritrust Order #{order.order_number}: Driver {delivery.driver_name or 'assigned'} ({delivery.vehicle_reg or 'N/A'}) will handle transport."
    _sms(farmer, msg)
    _sms(buyer, msg)


def _notify_pickup_in_progress(db: Session, order_id: uuid.UUID):
    _, buyer, order = _get_parties(db, order_id)
    _sms(buyer, f"ZimAgritrust Order #{order.order_number}: Pickup is in progress at the farm.")


def _notify_pickup_completed(db: Session, order_id: uuid.UUID, eta: Optional[datetime]):
    farmer, buyer, order = _get_parties(db, order_id)
    eta_str = eta.strftime("%d %b %H:%M") if eta else "TBD"
    _sms(farmer, f"ZimAgritrust Order #{order.order_number}: Goods picked up successfully.")
    _sms(buyer,  f"ZimAgritrust Order #{order.order_number}: Goods picked up. ETA: {eta_str}.")


def _notify_delay(db: Session, order_id: uuid.UUID, new_eta: Optional[datetime]):
    _, buyer, order = _get_parties(db, order_id)
    eta_str = new_eta.strftime("%d %b %H:%M") if new_eta else "TBD"
    _sms(buyer, f"ZimAgritrust Order #{order.order_number}: ⚠️ Delivery delayed. New ETA: {eta_str}.")


def _notify_arrival(db: Session, order_id: uuid.UUID):
    farmer, buyer, order = _get_parties(db, order_id)
    _sms(buyer,  f"ZimAgritrust Order #{order.order_number}: 🚚 Driver has arrived at your location.")
    _sms(farmer, f"ZimAgritrust Order #{order.order_number}: Goods delivered to buyer.")


def _notify_delivery_completed(db: Session, order_id: uuid.UUID, deadline: Optional[datetime]):
    farmer, buyer, order = _get_parties(db, order_id)
    deadline_str = deadline.strftime("%d %b %H:%M") if deadline else "24 hours"
    _sms(farmer, f"ZimAgritrust Order #{order.order_number}: Goods handed over. Awaiting buyer confirmation.")
    _sms(buyer,  f"ZimAgritrust Order #{order.order_number}: Goods delivered. You have until {deadline_str} to inspect and confirm or raise a dispute.")


def _notify_buyer_confirmed(db: Session, order_id: uuid.UUID):
    farmer, buyer, order = _get_parties(db, order_id)
    _sms(farmer, f"ZimAgritrust Order #{order.order_number}: ✅ Buyer confirmed receipt. Payment is being released to your wallet.")
    _sms(buyer,  f"ZimAgritrust Order #{order.order_number}: ✅ Transaction complete. Thank you!")


def _notify_auto_confirmed(db: Session, order_id: uuid.UUID):
    farmer, buyer, order = _get_parties(db, order_id)
    _sms(farmer, f"ZimAgritrust Order #{order.order_number}: ✅ Delivery auto-confirmed (24h window passed). Payment released.")
    _sms(buyer,  f"ZimAgritrust Order #{order.order_number}: ✅ Delivery auto-confirmed. Transaction complete.")
