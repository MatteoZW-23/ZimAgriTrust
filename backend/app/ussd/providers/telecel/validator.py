"""Telecel Request Validator."""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("ussd.provider.telecel.validator")

TELECEL_PHONE_PATTERN = re.compile(r"^(\+?263|0)73\d{7}$")


class TelecelValidator:
    """Validates Telecel USSD request payloads."""

    REQUIRED_FIELDS = ["sid", "phone"]

    def validate_payload(self, payload: dict) -> tuple[bool, str]:
        """Validate Telecel payload."""
        for field in self.REQUIRED_FIELDS:
            alt = {"sid": "session_id", "phone": "msisdn"}.get(field, "")
            if field not in payload and alt not in payload:
                return False, f"Missing field: {field}"

        phone = payload.get("phone", payload.get("msisdn", ""))
        normalized = phone.replace(" ", "").replace("-", "").replace("+", "")
        if normalized.startswith("263"):
            normalized = "0" + normalized[3:]
        if not TELECEL_PHONE_PATTERN.match(normalized) and not TELECEL_PHONE_PATTERN.match(f"+263{normalized[1:]}"):
            return False, "Invalid Telecel phone number"

        return True, ""

    def is_telecel_number(self, phone: str) -> bool:
        """Check if phone is a Telecel number."""
        normalized = phone.replace(" ", "").replace("-", "").replace("+", "")
        if normalized.startswith("263"):
            normalized = "0" + normalized[3:]
        return bool(TELECEL_PHONE_PATTERN.match(normalized))


telecel_validator = TelecelValidator()
