"""
NetOne USSD Adapter
====================
Handles NetOne Zimbabwe USSD callbacks.
NetOne is the second-largest network (~25% market share).

NetOne USSD behavior:
- Sends session_id, msisdn, ussd_string, short_code, msg_type
- msg_type: "initiation" for new, "response" for continue, "timeout" for abort
- Phone numbers prefixed with 26371XXXXXXX
- Session timeout: ~25 seconds
- Max response: 160 chars
"""
from __future__ import annotations

import hmac
import hashlib
import logging

from app.ussd.providers.common.base_adapter import BaseProviderAdapter
from app.ussd.providers.common.request_types import (
    NormalizedUSSDRequest,
    NormalizedUSSDResponse,
    ProviderName,
    SessionAction,
)

logger = logging.getLogger("ussd.provider.netone")


class NetOneAdapter(BaseProviderAdapter):
    """NetOne Zimbabwe USSD adapter."""

    provider_name = ProviderName.NETONE
    service_code = "*123#"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.webhook_secret = self.config.get("webhook_secret", "")
        self.max_response_chars = 160

    def normalize_request(self, raw_payload: dict) -> NormalizedUSSDRequest:
        """Convert NetOne callback to normalized format."""
        session_id = raw_payload.get("session_id", raw_payload.get("sessionId", ""))
        phone = raw_payload.get("msisdn", raw_payload.get("phone", ""))
        text = raw_payload.get("ussd_string", raw_payload.get("text", ""))
        service_code = raw_payload.get("short_code", raw_payload.get("service_code", self.service_code))
        msg_type = raw_payload.get("msg_type", raw_payload.get("type", ""))

        phone = self.normalize_phone(phone)
        action = self.detect_session_action(raw_payload)

        self.record_success()
        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=phone,
            text=text,
            service_code=service_code,
            provider=ProviderName.NETONE,
            action=action,
            raw_payload=raw_payload,
            is_new_session=(action == SessionAction.NEW),
            provider_metadata={"msg_type": msg_type},
        )

    def format_response(self, response: NormalizedUSSDResponse) -> dict:
        """Format response for NetOne expectations."""
        message = response.message

        if not message.startswith("CON") and not message.startswith("END"):
            if response.end_session:
                message = f"END {message}"
            else:
                message = f"CON {message}"

        if len(message) > self.max_response_chars:
            message = message[: self.max_response_chars - 3] + "..."

        # NetOne expects different response structure
        return {
            "session_id": response.session_id,
            "ussd_response": message,
            "session_end": response.end_session,
            "msg_type": "end" if response.end_session else "response",
        }

    def validate_signature(self, raw_payload: dict, headers: dict) -> bool:
        """Verify NetOne callback signature."""
        if not self.webhook_secret:
            return True

        signature = headers.get("X-NetOne-Signature", headers.get("x-netone-signature", ""))
        if not signature:
            logger.warning("Missing NetOne signature")
            return False

        payload_str = "|".join(str(v) for v in sorted(raw_payload.values()) if isinstance(v, (str, int)))
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(signature, expected)
        if not valid:
            self.record_error("signature_mismatch")
        return valid

    def detect_session_action(self, raw_payload: dict) -> SessionAction:
        """Detect action from NetOne msg_type field."""
        msg_type = raw_payload.get("msg_type", raw_payload.get("type", "")).lower()
        if msg_type in ("initiation", "new", "begin"):
            return SessionAction.NEW
        if msg_type in ("timeout", "abort", "cancel"):
            return SessionAction.TIMEOUT
        if msg_type in ("response", "continue", "input"):
            return SessionAction.CONTINUE
        # Fallback: empty text = new session
        text = raw_payload.get("ussd_string", raw_payload.get("text", ""))
        return SessionAction.NEW if not text else SessionAction.CONTINUE


netone_adapter = NetOneAdapter()
