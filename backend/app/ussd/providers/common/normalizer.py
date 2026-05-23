"""
Payload Normalizer
==================
Normalizes raw telco payloads into a consistent format.
Handles Zimbabwe-specific quirks:
- Phone number formats (0XX vs 263XX vs +263XX)
- Session ID formats (vary by provider)
- Text encoding issues
- Duplicate field names across providers
"""
from __future__ import annotations

import re
import time
import logging
from typing import Optional

from app.ussd.providers.common.request_types import (
    NormalizedUSSDRequest,
    ProviderName,
    SessionAction,
)

logger = logging.getLogger("ussd.normalizer")


class PayloadNormalizer:
    """
    Central normalizer for all Zimbabwe telco USSD payloads.
    Detects provider from payload structure and normalizes.
    """

    # Provider detection patterns
    ECONET_FIELDS = {"sessionId", "phoneNumber", "text", "serviceCode"}
    NETONE_FIELDS = {"session_id", "msisdn", "ussd_string", "short_code"}
    TELECEL_FIELDS = {"sid", "phone", "input", "code"}

    def detect_provider(self, payload: dict) -> ProviderName:
        """Auto-detect provider from payload structure."""
        keys = set(payload.keys())
        if self.ECONET_FIELDS.issubset(keys) or "sessionId" in keys:
            return ProviderName.ECONET
        if self.NETONE_FIELDS.issubset(keys) or "msisdn" in keys:
            return ProviderName.NETONE
        if self.TELECEL_FIELDS.issubset(keys) or "sid" in keys:
            return ProviderName.TELECEL
        # Default to Econet (most common in Zimbabwe)
        return ProviderName.ECONET

    def normalize(self, payload: dict, provider: ProviderName = None) -> NormalizedUSSDRequest:
        """Normalize any provider payload to standard format."""
        if provider is None:
            provider = self.detect_provider(payload)

        if provider == ProviderName.ECONET:
            return self._normalize_econet(payload)
        elif provider == ProviderName.NETONE:
            return self._normalize_netone(payload)
        elif provider == ProviderName.TELECEL:
            return self._normalize_telecel(payload)
        return self._normalize_generic(payload)

    def _normalize_econet(self, payload: dict) -> NormalizedUSSDRequest:
        """Normalize Econet payload format."""
        session_id = payload.get("sessionId", payload.get("session_id", ""))
        phone = payload.get("phoneNumber", payload.get("phone_number", ""))
        text = payload.get("text", "")
        service_code = payload.get("serviceCode", payload.get("service_code", "*123#"))
        network_code = payload.get("networkCode", "")

        # Econet signals new session with empty text
        is_new = not text
        action = SessionAction.NEW if is_new else SessionAction.CONTINUE

        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=self._normalize_phone(phone),
            text=text,
            service_code=service_code,
            provider=ProviderName.ECONET,
            action=action,
            timestamp=time.time(),
            raw_payload=payload,
            network_code=network_code,
            is_new_session=is_new,
        )

    def _normalize_netone(self, payload: dict) -> NormalizedUSSDRequest:
        """Normalize NetOne payload format."""
        session_id = payload.get("session_id", payload.get("sessionId", ""))
        phone = payload.get("msisdn", payload.get("phone", ""))
        text = payload.get("ussd_string", payload.get("text", ""))
        service_code = payload.get("short_code", payload.get("service_code", "*123#"))
        msg_type = payload.get("msg_type", payload.get("type", ""))

        # NetOne uses msg_type to signal session state
        if msg_type in ("initiation", "new", "1"):
            action = SessionAction.NEW
            is_new = True
        elif msg_type in ("timeout", "abort"):
            action = SessionAction.TIMEOUT
            is_new = False
        else:
            action = SessionAction.CONTINUE
            is_new = False

        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=self._normalize_phone(phone),
            text=text,
            service_code=service_code,
            provider=ProviderName.NETONE,
            action=action,
            timestamp=time.time(),
            raw_payload=payload,
            is_new_session=is_new,
            provider_metadata={"msg_type": msg_type},
        )

    def _normalize_telecel(self, payload: dict) -> NormalizedUSSDRequest:
        """Normalize Telecel payload format."""
        session_id = payload.get("sid", payload.get("session_id", ""))
        phone = payload.get("phone", payload.get("msisdn", ""))
        text = payload.get("input", payload.get("text", ""))
        service_code = payload.get("code", payload.get("service_code", "*123#"))
        session_type = payload.get("type", payload.get("session_type", ""))

        # Telecel uses 'type' field
        if session_type in ("begin", "new", "0"):
            action = SessionAction.NEW
            is_new = True
        elif session_type in ("end", "timeout"):
            action = SessionAction.TIMEOUT
            is_new = False
        else:
            action = SessionAction.CONTINUE
            is_new = False

        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=self._normalize_phone(phone),
            text=text,
            service_code=service_code,
            provider=ProviderName.TELECEL,
            action=action,
            timestamp=time.time(),
            raw_payload=payload,
            is_new_session=is_new,
            provider_metadata={"session_type": session_type},
        )

    def _normalize_generic(self, payload: dict) -> NormalizedUSSDRequest:
        """Fallback normalization for unknown formats."""
        session_id = (
            payload.get("session_id")
            or payload.get("sessionId")
            or payload.get("sid")
            or ""
        )
        phone = (
            payload.get("phone_number")
            or payload.get("phoneNumber")
            or payload.get("msisdn")
            or payload.get("phone")
            or ""
        )
        text = (
            payload.get("text")
            or payload.get("input")
            or payload.get("ussd_string")
            or ""
        )

        return NormalizedUSSDRequest(
            session_id=session_id,
            phone_number=self._normalize_phone(phone),
            text=text,
            service_code="*123#",
            provider=ProviderName.ECONET,
            action=SessionAction.NEW if not text else SessionAction.CONTINUE,
            timestamp=time.time(),
            raw_payload=payload,
            is_new_session=not text,
        )

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize Zimbabwe phone to +263 format."""
        if not phone:
            return ""
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            return f"+263{phone[1:]}"
        if phone.startswith("263"):
            return f"+{phone}"
        if phone.startswith("+263"):
            return phone
        return phone


# Module-level singleton
normalizer = PayloadNormalizer()
