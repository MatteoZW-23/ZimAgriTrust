"""
USSD Router
============
Maps incoming provider requests to the session manager.
Handles provider-specific payload normalization before processing.
"""
from __future__ import annotations

import logging
from typing import Any

from app.ussd.engine.session_manager import session_manager, SessionManager

logger = logging.getLogger("ussd.router")


class USSDRouter:
    """
    Routes normalized USSD requests to the session manager.
    Provider adapters normalize payloads before reaching this layer.
    """

    def __init__(self, manager: SessionManager = None):
        self.manager = manager or session_manager

    async def route(
        self,
        session_id: str,
        phone_number: str,
        text: str,
        provider: str,
        db: Any,
        service_code: str = "*123#",
        correlation_id: str = "",
    ) -> dict:
        """
        Route a normalized USSD request.
        
        Args:
            session_id: Telco-provided session identifier
            phone_number: Normalized E.164 phone number
            text: Full USSD text input (may contain * separators)
            provider: Provider name (econet, netone, telecel)
            db: Database session
            service_code: USSD service code (e.g. *123#)
            correlation_id: Request tracing ID
            
        Returns:
            Dict with 'message' and 'end_session' keys
        """
        # Extract latest input from accumulated text
        # Zimbabwe telcos send accumulated text: "1*2*1234" not just "1234"
        user_input = self._extract_latest_input(text)

        return await self.manager.process_request(
            session_id=session_id,
            phone_number=phone_number,
            user_input=user_input,
            provider=provider,
            db=db,
            correlation_id=correlation_id,
            service_code=service_code,
        )

    def _extract_latest_input(self, text: str) -> str:
        """
        Extract the latest user input from accumulated USSD text.
        Zimbabwe telcos accumulate: "" -> "1" -> "1*1234" -> "1*1234*2"
        We need only the latest segment.
        """
        if not text:
            return ""
        parts = [p for p in text.split("*") if p]
        return parts[-1] if parts else ""


# Module-level singleton
ussd_router = USSDRouter()
