"""
USSD Request/Response Types
============================
Normalized data structures for all Zimbabwe telco providers.
Provider adapters convert raw payloads to/from these types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProviderName(str, Enum):
    ECONET = "econet"
    NETONE = "netone"
    TELECEL = "telecel"


class SessionAction(str, Enum):
    """Telco session lifecycle actions."""
    NEW = "new"  # First request (dial)
    CONTINUE = "continue"  # Subsequent input
    TIMEOUT = "timeout"  # Session timed out
    CANCEL = "cancel"  # User cancelled
    ERROR = "error"  # Provider error


@dataclass
class NormalizedUSSDRequest:
    """Provider-agnostic USSD request."""
    session_id: str
    phone_number: str  # Always +263 format
    text: str  # Accumulated input (e.g. "1*2*1234")
    service_code: str  # e.g. "*123#"
    provider: ProviderName
    action: SessionAction
    correlation_id: str = ""
    timestamp: float = 0.0
    raw_payload: dict = field(default_factory=dict)
    provider_metadata: dict = field(default_factory=dict)
    network_code: str = ""  # MCC+MNC
    is_new_session: bool = False


@dataclass
class NormalizedUSSDResponse:
    """Provider-agnostic USSD response."""
    message: str
    end_session: bool = False
    session_id: str = ""
    correlation_id: str = ""

    def to_provider_format(self, provider: ProviderName) -> dict:
        """Convert to provider-specific response format."""
        if provider == ProviderName.ECONET:
            return {
                "response": self.message,
                "endSession": self.end_session,
            }
        elif provider == ProviderName.NETONE:
            return {
                "ussd_response": self.message,
                "session_end": self.end_session,
                "session_id": self.session_id,
            }
        elif provider == ProviderName.TELECEL:
            return {
                "msg": self.message,
                "end": self.end_session,
                "sid": self.session_id,
            }
        return {"message": self.message, "end_session": self.end_session}


@dataclass
class ProviderHealth:
    """Provider health status."""
    provider: ProviderName
    healthy: bool
    latency_ms: int = 0
    last_error: str = ""
    error_count: int = 0
    last_check: float = 0.0
