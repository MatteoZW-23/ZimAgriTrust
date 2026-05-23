"""NetOne Payload Mapper — maps NetOne-specific fields."""
from __future__ import annotations


class NetOnePayloadMapper:
    """Maps NetOne payload fields."""

    NETWORK_CODES = {"64504": "netone_primary"}

    @staticmethod
    def extract_session_id(payload: dict) -> str:
        return payload.get("session_id", payload.get("sessionId", ""))

    @staticmethod
    def extract_phone(payload: dict) -> str:
        return payload.get("msisdn", payload.get("phone", ""))

    @staticmethod
    def extract_text(payload: dict) -> str:
        return payload.get("ussd_string", payload.get("text", ""))

    @staticmethod
    def extract_latest_input(text: str) -> str:
        if not text:
            return ""
        parts = text.split("*")
        return parts[-1] if parts else ""

    @staticmethod
    def build_response_payload(message: str, end_session: bool, session_id: str = "") -> dict:
        return {
            "session_id": session_id,
            "ussd_response": message,
            "session_end": end_session,
            "msg_type": "end" if end_session else "response",
        }


netone_mapper = NetOnePayloadMapper()
