"""
Base Provider Adapter
=====================
Abstract base class for all Zimbabwe telco USSD adapters.
Enforces consistent interface across Econet, NetOne, Telecel.
"""
from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.ussd.providers.common.request_types import (
    NormalizedUSSDRequest,
    NormalizedUSSDResponse,
    ProviderName,
    ProviderHealth,
    SessionAction,
)

logger = logging.getLogger("ussd.provider.base")


class BaseProviderAdapter(ABC):
    """
    Abstract base for Zimbabwe telco USSD adapters.
    All providers must implement:
    - normalize_request: Convert raw payload to NormalizedUSSDRequest
    - format_response: Convert NormalizedUSSDResponse to provider format
    - validate_signature: Verify telco callback authenticity
    - get_health: Check provider connectivity
    """

    provider_name: ProviderName
    service_code: str = "*123#"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._error_count = 0
        self._request_count = 0
        self._last_error = ""
        self._last_health_check = 0.0

    @abstractmethod
    def normalize_request(self, raw_payload: dict) -> NormalizedUSSDRequest:
        """
        Convert provider-specific payload to normalized format.
        Must handle all provider quirks and edge cases.
        """
        ...

    @abstractmethod
    def format_response(self, response: NormalizedUSSDResponse) -> dict:
        """
        Convert normalized response to provider-specific format.
        Must include correct headers and structure for the telco.
        """
        ...

    @abstractmethod
    def validate_signature(self, raw_payload: dict, headers: dict) -> bool:
        """
        Verify the authenticity of an incoming telco callback.
        Each provider has different signature mechanisms.
        """
        ...

    @abstractmethod
    def detect_session_action(self, raw_payload: dict) -> SessionAction:
        """
        Determine the session action from the raw payload.
        Different providers signal new/continue/timeout differently.
        """
        ...

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +263 format."""
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

    def get_health(self) -> ProviderHealth:
        """Get provider health status."""
        return ProviderHealth(
            provider=self.provider_name,
            healthy=self._error_count < 10,
            latency_ms=0,
            last_error=self._last_error,
            error_count=self._error_count,
            last_check=self._last_health_check,
        )

    def record_error(self, error: str) -> None:
        """Record a provider error."""
        self._error_count += 1
        self._last_error = error
        logger.error(
            "Provider error",
            extra={"provider": self.provider_name.value, "error": error},
        )

    def record_success(self) -> None:
        """Record successful interaction."""
        self._request_count += 1
        if self._error_count > 0:
            self._error_count = max(0, self._error_count - 1)

    def get_stats(self) -> dict:
        """Get adapter statistics."""
        return {
            "provider": self.provider_name.value,
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
        }
