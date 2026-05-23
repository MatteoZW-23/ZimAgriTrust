"""Telecel Payload Mapper."""
from __future__ import annotations


class TelecelPayloadMapper:
    """Maps Telecel payload fields."""

    NETWORK_CODES = {"64503": "telecel_primary"}

    @staticmethod
    def extract_session_id(payload: dict) -> str:
        return payload.get("sid", payload.get("session_id", ""))

    @staticmethod
    def extract_phone(payload: dict) -> str:
        return payload.get("phone", payload.get("msisdn", ""))

    @staticmethod
    def extract_text(payload: dict) -> str:
        return payload.get("input", payload.get("text", ""))

    @staticmethod
    def extract_latest_input(text: str) -> str:
        if not text:
            return ""
        parts = text.split("*")
        return parts[-1] if parts else ""

    @staticmethod
    def build_response_payload(message: str, end_session: bool, session_id: str = "") -> dict:
        return {"sid": session_id, "msg": message, "end": end_session}


telecel_mapper = TelecelPayloadMapper()
