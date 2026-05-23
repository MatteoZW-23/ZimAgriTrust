"""
Econet Payload Mapper
=====================
Maps Econet-specific payload fields to and from normalized format.
Handles Econet quirks like networkCode, concatenated text, etc.
"""
from __future__ import annotations

from typing import Optional


class EconetPayloadMapper:
    """Maps Econet payload fields."""

    # Econet network codes
    NETWORK_CODES = {
        "64501": "econet_primary",
        "64502": "econet_secondary",
    }

    @staticmethod
    def extract_session_id(payload: dict) -> str:
        """Extract session ID from Econet payload."""
        return payload.get("sessionId", payload.get("session_id", ""))

    @staticmethod
    def extract_phone(payload: dict) -> str:
        """Extract phone number from Econet payload."""
        return payload.get("phoneNumber", payload.get("phone_number", ""))

    @staticmethod
    def extract_text(payload: dict) -> str:
        """Extract USSD text from Econet payload."""
        return payload.get("text", "")

    @staticmethod
    def extract_service_code(payload: dict) -> str:
        """Extract service code from Econet payload."""
        return payload.get("serviceCode", payload.get("service_code", "*123#"))

    @staticmethod
    def extract_latest_input(text: str) -> str:
        """Extract only the latest input from accumulated Econet text."""
        if not text:
            return ""
        parts = text.split("*")
        return parts[-1] if parts else ""

    @staticmethod
    def build_response_payload(message: str, end_session: bool) -> dict:
        """Build Econet-compatible response payload."""
        return {
            "response": message,
            "endSession": end_session,
        }

    @staticmethod
    def get_network_name(code: str) -> str:
        """Get human-readable network name from code."""
        return EconetPayloadMapper.NETWORK_CODES.get(code, "econet_unknown")


econet_mapper = EconetPayloadMapper()
