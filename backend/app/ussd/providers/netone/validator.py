"""NetOne Request Validator."""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("ussd.provider.netone.validator")

NETONE_PHONE_PATTERN = re.compile(r"^(\+?263|0)71\d{7}$")


class NetOneValidator:
    """Validates NetOne USSD request payloads."""

    REQUIRED_FIELDS = ["session_id", "msisdn"]

    def validate_payload(self, payload: dict) -> tuple[bool, str]:
        """Validate NetOne payload."""
        for field in self.REQUIRED_FIELDS:
            alt = {"session_id": "sessionId", "msisdn": "phone"}.get(field, "")
            if field not in payload and alt not in payload:
                return False, f"Missing field: {field}"

        phone = payload.get("msisdn", payload.get("phone", ""))
        normalized = phone.replace(" ", "").replace("-", "")
        if normalized.startswith("+"):
            normalized = normalized[1:]
        if normalized.startswith("263"):
            normalized = "0" + normalized[3:]
        if not NETONE_PHONE_PATTERN.match(normalized) and not NETONE_PHONE_PATTERN.match(f"+263{normalized[1:]}"):
            return False, "Invalid NetOne phone number"

        return True, ""

    def is_netone_number(self, phone: str) -> bool:
        """Check if phone is a NetOne number."""
        normalized = phone.replace(" ", "").replace("-", "").replace("+", "")
        if normalized.startswith("263"):
            normalized = "0" + normalized[3:]
        return bool(NETONE_PHONE_PATTERN.match(normalized))


netone_validator = NetOneValidator()
