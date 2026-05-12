"""
Two-key escrow release.

Releasing escrowed funds requires BOTH:

  Key 1 — Platform signature (HMAC over the order release intent).
  Key 2 — Admin OTP delivered out-of-band (SMS) to the admin's phone.

Flow:
    request_release(...)  →  generates platform signature, generates OTP,
                              sends OTP via SMS to admin, stores hash in cache.
    confirm_release(...)  →  validates OTP, validates platform signature,
                              ensures any required AdminApproval is FULLY_APPROVED,
                              then delegates to escrow_service.release_payment.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.transaction import Order, OrderStatus
from app.models.user import User
from app.services.admin_approval_service import (
    enforce_financial_hours,
    is_fully_approved,
)
from app.services.audit_chain_service import append_audit
from app.services.cache_service import cache_service
from app.services.transaction_signing_service import sign_transaction, verify_transaction

logger = logging.getLogger(__name__)


def _otp_cache_key(order_id: str, admin_id: str) -> str:
    return f"escrow:otp:{order_id}:{admin_id}"


def _intent_cache_key(order_id: str) -> str:
    return f"escrow:intent:{order_id}"


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


async def request_release(
    db: Session,
    *,
    order_id: UUID,
    admin: User,
) -> dict:
    """Step 1 — generate platform signature + admin OTP."""
    enforce_financial_hours(admin)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {OrderStatus.ESCROW_HELD, OrderStatus.DELIVERED, OrderStatus.DISPUTED}:
        raise HTTPException(status_code=400, detail=f"Cannot release escrow in state {order.status.value}")

    # If amount triggers approval workflow, require it first
    threshold = settings.ESCROW_TWO_KEY_REQUIRED_THRESHOLD_USD
    if float(order.total_amount) > settings.MULTI_APPROVAL_TXN_THRESHOLD_USD:
        if not is_fully_approved(db, resource_type="order", resource_id=str(order.id)):
            raise HTTPException(
                status_code=403,
                detail="Multi-admin approval required before escrow release for this amount",
            )

    # Key 1: platform signature over the release intent
    signature, payload = sign_transaction(
        user_id=str(admin.id),
        txn_type="ESCROW_RELEASE_INTENT",
        amount=float(order.total_amount),
        currency=order.currency,
        order_id=str(order.id),
        extra={"admin_id": str(admin.id), "threshold": threshold},
    )
    await cache_service.set(
        _intent_cache_key(str(order.id)),
        {"signature": signature, "payload": payload, "admin_id": str(admin.id)},
        expire=settings.ESCROW_ADMIN_OTP_TTL_SECONDS,
    )

    # Key 2: OTP, hashed in cache; plaintext sent via SMS
    otp = _generate_otp()
    await cache_service.set(
        _otp_cache_key(str(order.id), str(admin.id)),
        _hash_otp(otp),
        expire=settings.ESCROW_ADMIN_OTP_TTL_SECONDS,
    )

    _send_otp_sms(admin, order, otp)

    append_audit(
        db,
        table_name="orders",
        record_id=str(order.id),
        operation="ESCROW_RELEASE_REQUEST",
        payload={
            "order_id": str(order.id),
            "amount": float(order.total_amount),
            "currency": order.currency,
            "admin_id": str(admin.id),
        },
        actor_id=str(admin.id),
        actor_role=admin.role.value,
    )
    db.commit()

    return {
        "status": "OTP_SENT",
        "order_id": str(order.id),
        "expires_in": settings.ESCROW_ADMIN_OTP_TTL_SECONDS,
        "amount": float(order.total_amount),
        "currency": order.currency,
    }


async def confirm_release(
    db: Session,
    *,
    order_id: UUID,
    admin: User,
    otp: str,
    handover_code: Optional[str] = None,
) -> Order:
    """Step 2 — validate OTP + signature, then perform the release."""
    enforce_financial_hours(admin)

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate OTP (Key 2)
    cached_hash = await cache_service.get(_otp_cache_key(str(order.id), str(admin.id)))
    if not cached_hash:
        raise HTTPException(status_code=400, detail="OTP expired or not requested")
    if not hmac.compare_digest(cached_hash, _hash_otp(otp.strip())):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Validate platform signature (Key 1)
    intent = await cache_service.get(_intent_cache_key(str(order.id)))
    if not intent or intent.get("admin_id") != str(admin.id):
        raise HTTPException(status_code=400, detail="Release intent missing or mismatched")
    if not verify_transaction(signature=intent["signature"], payload=intent["payload"]):
        raise HTTPException(status_code=400, detail="Platform signature verification failed")

    # Both keys validated → execute the release through the existing service
    from app.services import escrow_service  # local import to avoid cycles
    released = escrow_service.release_payment(db, order, handover_code=handover_code)

    # Append audit chain entry for the actual release
    append_audit(
        db,
        table_name="orders",
        record_id=str(order.id),
        operation="ESCROW_RELEASE_EXECUTED",
        payload={
            "order_id": str(order.id),
            "amount": float(released.total_amount),
            "currency": released.currency,
            "admin_id": str(admin.id),
            "platform_signature": intent["signature"],
        },
        actor_id=str(admin.id),
        actor_role=admin.role.value,
    )
    db.commit()

    # Clean up
    await cache_service.delete(_otp_cache_key(str(order.id), str(admin.id)))
    await cache_service.delete(_intent_cache_key(str(order.id)))

    _notify_parties_release(released)
    return released


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _send_otp_sms(admin: User, order: Order, otp: str) -> None:
    try:
        from app.services.sms_service import sms_service
        if not getattr(admin, "phone_number", None):
            logger.warning("Admin %s has no phone — cannot send escrow OTP", admin.id)
            return
        sms_service.send_sms(  # type: ignore[attr-defined]
            admin.phone_number,
            f"[ZimAgriTrust] Escrow release OTP for order {order.order_number or order.id}: {otp}. "
            f"Expires in {settings.ESCROW_ADMIN_OTP_TTL_SECONDS // 60}m.",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Escrow OTP SMS failed: %s", exc)


def _notify_parties_release(order: Order) -> None:
    try:
        from app.services.sms_service import sms_service
        for u in (order.buyer, order.seller):
            if u and getattr(u, "phone_number", None):
                sms_service.send_sms(  # type: ignore[attr-defined]
                    u.phone_number,
                    f"[ZimAgriTrust] Escrow released for order {order.order_number or order.id}.",
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Escrow release SMS failed: %s", exc)
