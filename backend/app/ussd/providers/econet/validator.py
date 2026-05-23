"""
Econet Request Validator
========================
Validates incoming Econet USSD callbacks for completeness and security.
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("ussd.provider.econet.validator")

# Econet phone pattern: +263 77/78 XXXXXXX
ECONET_PHONE_PATTERN = re.compile(r"^(\+?263|0)7[78]\d{7}$")


class EconetValidator:
    """Validates Econet USSD request payloads."""

    REQUIRED_FIELDS = ["sessionId", "phoneNumber", "serviceCode"]
    MAX_TEXT_LENGTH = 182
    MAX_SESSION_ID_LENGTH = 64

    def validate_payload(self, payload: dict) -> tuple[bool, str]:
        """Validate complete Econet payload. Returns (valid, error_message)."""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in payload or not payload[field]:
                return False, f"Missing required field: {field}"

        # Validate session ID
        session_id = payload.get("sessionId", "")
        if len(session_id) > self.MAX_SESSION_ID_LENGTH:
            return False, "Session ID too long"
        if not re.match(r"^[a-zA-Z0-9\-_]+$", session_id):
            return False, "Invalid session ID format"

        # Validate phone number
        phone = payload.get("phoneNumber", "")
        normalized = phone.replace(" ", "").replace("-", "")
        if not ECONET_PHONE_PATTERN.match(normalized):
            return False, "Invalid Econet phone number"

        # Validate text length
        text = payload.get("text", "")
        if len(text) > self.MAX_TEXT_LENGTH:
            return False, "Text input too long"

        # Validate service code
        service_code = payload.get("serviceCode", "")
        if not re.match(r"^\*\d{2,5}#$", service_code):
            return False, "Invalid service code format"

        return True, ""

    def is_econet_number(self, phone: str) -> bool:
        """Check if phone is an Econet number."""
        normalized = phone.replace(" ", "").replace("-", "").replace("+", "")
        if normalized.startswith("263"):
            normalized = "0" + normalized[3:]
        return bool(ECONET_PHONE_PATTERN.match(normalized)) or bool(
            ECONET_PHONE_PATTERN.match(f"+263{normalized[1:]}" if normalized.startswith("0") else normalized)
        )


econet_validator = EconetValidator()
