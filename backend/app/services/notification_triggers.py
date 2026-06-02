"""Safe notification trigger wrappers used by business services."""
from __future__ import annotations

import logging
from typing import Optional

from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _send(phone_number: Optional[str], message: str) -> bool:
    if not phone_number:
        return False
    try:
        return bool(NotificationService._send_sms(phone_number, message))
    except Exception as exc:
        logger.warning("Notification trigger failed: %s", exc)
        return False


def deposit_completed(phone_number: Optional[str], amount: float, channel: str, reference: Optional[str] = None) -> bool:
    ref = f" Ref: {reference}." if reference else ""
    return _send(phone_number, f"ZimAgriTrust: Deposit of ${amount:.2f} via {channel} received.{ref}")


def deposit_failed(phone_number: Optional[str], reason: str, reference: Optional[str] = None) -> bool:
    ref = f" Ref: {reference}." if reference else ""
    return _send(phone_number, f"ZimAgriTrust: Deposit failed.{ref} Reason: {reason}.")


def deposit_refund_processed(phone_number: Optional[str], net_amount: float, fee: float) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Deposit refund processed. Net: ${net_amount:.2f}. Fee: ${fee:.2f}.")


def cash_collected_by_agent(buyer_phone: Optional[str], agent_name: str, amount: float) -> bool:
    return _send(buyer_phone, f"ZimAgriTrust: Agent {agent_name} collected ${amount:.2f} cash deposit.")


def input_listing_verified(phone_number: Optional[str], product_name: str) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Your input listing '{product_name}' has been verified.")


def input_listing_rejected(phone_number: Optional[str], product_name: str, reason: str) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Your input listing '{product_name}' was rejected. Reason: {reason}.")


def input_offer_received(phone_number: Optional[str], product_name: str, quantity: float, price: float) -> bool:
    return _send(phone_number, f"ZimAgriTrust: New offer for {quantity:g} units of {product_name} at ${price:.2f}.")


def input_offer_accepted(phone_number: Optional[str], product_name: str, total: float, order_ref: str) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Offer accepted for {product_name}. Total ${total:.2f}. Order {order_ref}.")


def input_offer_rejected(phone_number: Optional[str], product_name: str, reason: Optional[str] = None) -> bool:
    suffix = f" Reason: {reason}." if reason else ""
    return _send(phone_number, f"ZimAgriTrust: Offer for {product_name} was rejected.{suffix}")


def input_order_shipped(phone_number: Optional[str], order_ref: str, tracking_number: Optional[str] = None) -> bool:
    suffix = f" Tracking: {tracking_number}." if tracking_number else ""
    return _send(phone_number, f"ZimAgriTrust: Input order {order_ref} has shipped.{suffix}")


def input_order_completed(phone_number: Optional[str], order_ref: str, payout_amount: float) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Input order {order_ref} completed. Payout ${payout_amount:.2f}.")


def input_listing_expiry_warning(phone_number: Optional[str], product_name: str, days_left: int) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Listing '{product_name}' expires in {days_left} days.")


def input_listing_expired(phone_number: Optional[str], product_name: str) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Listing '{product_name}' has expired.")


def input_low_stock(phone_number: Optional[str], product_name: str, remaining_quantity: float) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Low stock alert for {product_name}. Remaining: {remaining_quantity:g}.")


def input_listing_reported(phone_number: Optional[str], product_name: str, reason: str) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Listing '{product_name}' was reported. Reason: {reason}.")


def input_price_alert_hit(phone_number: Optional[str], product_name: str, old_price: float, new_price: float) -> bool:
    return _send(phone_number, f"ZimAgriTrust: Price alert for {product_name}. ${old_price:.2f} -> ${new_price:.2f}.")
