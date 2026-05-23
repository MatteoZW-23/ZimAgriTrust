"""
Econet USSD Adapter
====================
Handles Econet Wireless Zimbabwe USSD callbacks.
Econet is the largest mobile network in Zimbabwe (~65% market share).

Econet USSD behavior:
- Sends sessionId, phoneNumber, text, serviceCode, networkCode
- Text is accumulated (e.g. "1*2*1234")
- Empty text = new session
- Session timeout: ~30 seconds
- Max response: 182 chars
- Supports CON/END prefixes
"""
from __future__ import annotations

import hmac
import hashlib
import logging
from typing import Any

from app.ussd.providers.common.base_adapter import BaseProviderAdapter
from app.ussd.providers.common.request_types import (
    NormalizedUSSDRequest,
    NormalizedUSSDResponse,
    ProviderName,
    SessionAction,
)

logger = logging.getLogger("ussd.provider.econet")


class EconetAdapter(BaseProviderAdapter):
    """Econet Wireless Zimbabwe USSD adapter."""

    provider_name = ProviderName.ECONET
    service_code = "*123#"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.webhook_secret = self.config.get("webhook_secret", "")
        self.max_response_chars = 182

    def normalize_request(self, raw_payload: dict) -> NormalizedUSSDRequest:
        """Convert Econet callback payload to normalized format."""
        session_id = raw_payload.get("sessionId", "")
        phone = raw_payload.get("phoneNumber", "")
        text = raw_payload.get("text", "")
        service_code = raw_payload.get("serviceCode", self.service_code)
        network_code = raw_payload.get("networkCode", "64501")  # Econet MCC+MNC

        # Normalize phone to +263 format
        phone = self.normalize_phone(phone)

        # Determine session action
        action = self.detect_session_action(raw_payload)

        self.record_success()
        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=phone,
            text=text,
            service_code=service_code,
            provider=ProviderName.ECONET,
            action=action,
            raw_payload=raw_payload,
            network_code=network_code,
            is_new_session=(action == SessionAction.NEW),
        )

    def format_response(self, response: NormalizedUSSDResponse) -> dict:
        """Format response for Econet callback expectations."""
        message = response.message

        # Ensure proper prefix
        if not message.startswith("CON") and not message.startswith("END"):
            if response.end_session:
                message = f"END {message}"
            else:
                message = f"CON {message}"

        # Truncate to Econet max
        if len(message) > self.max_response_chars:
            message = message[: self.max_response_chars - 3] + "..."

        return {
            "response": message,
            "endSession": response.end_session,
        }

    def validate_signature(self, raw_payload: dict, headers: dict) -> bool:
        """Verify Econet callback signature."""
        if not self.webhook_secret:
            # No secret configured — skip validation (dev mode)
            return True

        signature = headers.get("X-Econet-Signature", headers.get("x-econet-signature", ""))
        if not signature:
            logger.warning("Missing Econet signature header")
            return False

        # Compute expected signature
        payload_str = "&".join(f"{k}={v}" for k, v in sorted(raw_payload.items()))
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(signature, expected)
        if not valid:
            logger.warning("Invalid Econet signature")
            self.record_error("signature_mismatch")
        return valid

    def detect_session_action(self, raw_payload: dict) -> SessionAction:
        """Detect session action from Econet payload."""
        text = raw_payload.get("text", "")
        session_type = raw_payload.get("type", "")

        if session_type == "timeout":
            return SessionAction.TIMEOUT
        if session_type == "cancel":
            return SessionAction.CANCEL
        if not text:
            return SessionAction.NEW
        return SessionAction.CONTINUE


# Module-level instance
econet_adapter = EconetAdapter()
