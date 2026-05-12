"""
Notification trigger helpers for deposits + input marketplace.

These are best-effort, never raise — failures are logged and swallowed so
business logic transactions are never rolled back by SMS/WhatsApp errors.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _sms(phone: Optional[str], message: str) -> None:
    if not phone:
        return
    try:
        from app.services.sms_service import sms_service
        sms_service.send_sms(phone, message)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001
        logger.warning("notification SMS failed phone=%s err=%s", phone, exc)


# ---------------------------------------------------------------------------
# Deposit notifications
# ---------------------------------------------------------------------------

def deposit_completed(user_phone: Optional[str], amount: float, channel: str, ref: str) -> None:
    _sms(user_phone, f"[ZimAgriTrust] Deposit ${amount:.2f} via {channel} confirmed. Ref {ref}.")


def deposit_failed(user_phone: Optional[str], reason: str, ref: str) -> None:
    _sms(user_phone, f"[ZimAgriTrust] Deposit {ref} failed: {reason}. No funds debited.")


def deposit_refund_processed(user_phone: Optional[str], net: float, fee: float) -> None:
    _sms(
        user_phone,
        f"[ZimAgriTrust] Refund processed: ${net:.2f} (fee ${fee:.2f}) returned to your wallet.",
    )


def cash_collected_by_agent(buyer_phone: Optional[str], agent_name: str, amount: float) -> None:
    _sms(
        buyer_phone,
        f"[ZimAgriTrust] Agent {agent_name} confirmed receipt of ${amount:.2f} cash. Funds land within 30 minutes.",
    )


# ---------------------------------------------------------------------------
# Input marketplace notifications
# ---------------------------------------------------------------------------

def input_listing_verified(seller_phone: Optional[str], product: str) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] Your input listing '{product}' is now VERIFIED and live.")


def input_listing_rejected(seller_phone: Optional[str], product: str, reason: str) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] Your input listing '{product}' was rejected: {reason}")


def input_offer_received(seller_phone: Optional[str], product: str, qty: float, price: float) -> None:
    _sms(
        seller_phone,
        f"[ZimAgriTrust] New offer on '{product}': {qty} units @ ${price:.2f}. Open the app to respond.",
    )


def input_offer_accepted(buyer_phone: Optional[str], product: str, total: float, order_no: str) -> None:
    _sms(
        buyer_phone,
        f"[ZimAgriTrust] Offer on '{product}' ACCEPTED. Total ${total:.2f} held in escrow. Order {order_no}.",
    )


def input_offer_rejected(buyer_phone: Optional[str], product: str, reason: Optional[str]) -> None:
    suffix = f" Reason: {reason}." if reason else ""
    _sms(buyer_phone, f"[ZimAgriTrust] Your offer on '{product}' was rejected.{suffix}")


def input_order_shipped(buyer_phone: Optional[str], order_no: str, tracking: Optional[str]) -> None:
    track = f" Tracking: {tracking}." if tracking else ""
    _sms(buyer_phone, f"[ZimAgriTrust] Order {order_no} shipped.{track}")


def input_order_completed(seller_phone: Optional[str], order_no: str, payout: float) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] Order {order_no} completed. ${payout:.2f} released to wallet.")


def input_listing_expiry_warning(seller_phone: Optional[str], product: str, days: int) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] '{product}' expires in {days} day(s). Update or relist.")


def input_listing_expired(seller_phone: Optional[str], product: str) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] '{product}' has expired and was removed from browse.")


def input_low_stock(seller_phone: Optional[str], product: str, remaining: float) -> None:
    _sms(seller_phone, f"[ZimAgriTrust] Low stock on '{product}': only {remaining:g} units left.")


def input_listing_reported(admin_phone: Optional[str], product: str, reason: str) -> None:
    _sms(admin_phone, f"[ZimAgriTrust] Input '{product}' reported as {reason}. Review queue.")


def input_price_alert_hit(buyer_phone: Optional[str], product: str, price: float, target: float) -> None:
    _sms(
        buyer_phone,
        f"[ZimAgriTrust] Price alert: '{product}' now ${price:.2f} (target ${target:.2f}).",
    )
