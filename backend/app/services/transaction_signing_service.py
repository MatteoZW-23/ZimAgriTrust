"""
Transaction signing service.

Every fund-moving operation MUST be:
  1. Signed via `sign_transaction(...)` before persistence.
  2. Verified via `verify_transaction(...)` before any database mutation
     that releases funds (escrow release, refund, withdrawal, payout).

The signature binds the immutable economic fields:
  user_id, type, amount, currency, order_id, nonce, timestamp.

Algorithm: HMAC-SHA256 over a canonical JSON payload (sorted keys, no whitespace).
Key:       settings.effective_transaction_signing_key (separate from main SECRET_KEY).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Optional

from app.core.config import settings


SIGNATURE_VERSION = "v1"
MAX_CLOCK_SKEW_SECONDS = 300  # 5 minutes


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _key() -> bytes:
    return settings.effective_transaction_signing_key.encode("utf-8")


def make_nonce() -> str:
    """Cryptographically random nonce. Persist it on the txn to prevent replay."""
    return secrets.token_hex(16)


def build_payload(
    *,
    user_id: str,
    txn_type: str,
    amount: float,
    currency: str,
    order_id: Optional[str] = None,
    nonce: str,
    timestamp: int,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "v": SIGNATURE_VERSION,
        "user_id": str(user_id),
        "type": txn_type,
        "amount": round(float(amount), 2),
        "currency": currency,
        "nonce": nonce,
        "ts": int(timestamp),
    }
    if order_id is not None:
        payload["order_id"] = str(order_id)
    if extra:
        # Only allow primitives in extras to keep canonicalisation deterministic
        for k, v in sorted(extra.items()):
            if isinstance(v, (str, int, float, bool)) or v is None:
                payload[f"x_{k}"] = v
    return payload


def sign_payload(payload: dict[str, Any]) -> str:
    body = _canonical(payload).encode("utf-8")
    return hmac.new(_key(), body, hashlib.sha256).hexdigest()


def sign_transaction(
    *,
    user_id: str,
    txn_type: str,
    amount: float,
    currency: str = "USD",
    order_id: Optional[str] = None,
    nonce: Optional[str] = None,
    timestamp: Optional[int] = None,
    extra: Optional[dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Returns (signature, payload) — store both with the transaction."""
    payload = build_payload(
        user_id=user_id,
        txn_type=txn_type,
        amount=amount,
        currency=currency,
        order_id=order_id,
        nonce=nonce or make_nonce(),
        timestamp=timestamp or int(time.time()),
        extra=extra,
    )
    return sign_payload(payload), payload


def verify_signature(payload: dict[str, Any], signature: str) -> bool:
    if not signature or not payload:
        return False
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)


def verify_transaction(
    *,
    signature: str,
    payload: dict[str, Any],
    enforce_clock_skew: bool = True,
) -> bool:
    """
    Full verification: signature + freshness. Caller is responsible for
    nonce-replay protection (lookup by nonce in transactions table or Redis SETNX).
    """
    if not verify_signature(payload, signature):
        return False
    if enforce_clock_skew:
        ts = int(payload.get("ts", 0))
        if abs(int(time.time()) - ts) > MAX_CLOCK_SKEW_SECONDS:
            return False
    return True


def sign_admin_decision(
    *,
    actor_id: str,
    action: str,
    resource_id: str,
    decision: str,
    amount: Optional[float] = None,
    timestamp: Optional[int] = None,
) -> str:
    """Sign an admin approval/rejection decision. Stored on AdminApproval row."""
    payload = {
        "v": SIGNATURE_VERSION,
        "actor": str(actor_id),
        "action": action,
        "resource": str(resource_id),
        "decision": decision,
        "ts": int(timestamp or time.time()),
    }
    if amount is not None:
        payload["amount"] = round(float(amount), 2)
    return sign_payload(payload)
