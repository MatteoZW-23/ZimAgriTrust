"""
Telecel USSD Adapter
====================
Handles Telecel Zimbabwe USSD callbacks.
Telecel is the third network (~10% market share).

Telecel USSD behavior:
- Sends sid, phone, input, code, type
- type: "begin" for new, "continue" for input, "end" for timeout
- Phone numbers: 26373XXXXXXX
- Session timeout: ~20 seconds
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

logger = logging.getLogger("ussd.provider.telecel")


class TelecelAdapter(BaseProviderAdapter):
    """Telecel Zimbabwe USSD adapter."""

    provider_name = ProviderName.TELECEL
    service_code = "*123#"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.webhook_secret = self.config.get("webhook_secret", "")
        self.max_response_chars = 160

    def normalize_request(self, raw_payload: dict) -> NormalizedUSSDRequest:
        """Convert Telecel callback to normalized format."""
        session_id = raw_payload.get("sid", raw_payload.get("session_id", ""))
        phone = raw_payload.get("phone", raw_payload.get("msisdn", ""))
        text = raw_payload.get("input", raw_payload.get("text", ""))
        service_code = raw_payload.get("code", raw_payload.get("service_code", self.service_code))
        session_type = raw_payload.get("type", raw_payload.get("session_type", ""))

        phone = self.normalize_phone(phone)
        action = self.detect_session_action(raw_payload)

        self.record_success()
        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=phone,
            text=text,
            service_code=service_code,
            provider=ProviderName.TELECEL,
            action=action,
            raw_payload=raw_payload,
            is_new_session=(action == SessionAction.NEW),
            provider_metadata={"session_type": session_type},
        )

    def format_response(self, response: NormalizedUSSDResponse) -> dict:
        """Format response for Telecel expectations."""
        message = response.message

        if not message.startswith("CON") and not message.startswith("END"):
            if response.end_session:
                message = f"END {message}"
            else:
                message = f"CON {message}"

        if len(message) > self.max_response_chars:
            message = message[: self.max_response_chars - 3] + "..."

        return {
            "sid": response.session_id,
            "msg": message,
            "end": response.end_session,
        }

    def validate_signature(self, raw_payload: dict, headers: dict) -> bool:
        """Verify Telecel callback signature."""
        if not self.webhook_secret:
            return True

        signature = headers.get("X-Telecel-Sig", headers.get("x-telecel-sig", ""))
        if not signature:
            logger.warning("Missing Telecel signature")
            return False

        payload_str = "|".join(f"{k}={v}" for k, v in sorted(raw_payload.items()))
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
        """Detect action from Telecel type field."""
        session_type = raw_payload.get("type", raw_payload.get("session_type", "")).lower()
        if session_type in ("begin", "new", "start"):
            return SessionAction.NEW
        if session_type in ("end", "timeout", "abort"):
            return SessionAction.TIMEOUT
        if session_type in ("continue", "input", "response"):
            return SessionAction.CONTINUE
        text = raw_payload.get("input", raw_payload.get("text", ""))
        return SessionAction.NEW if not text else SessionAction.CONTINUE


telecel_adapter = TelecelAdapter()
