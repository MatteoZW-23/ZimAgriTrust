"""USSD Analytics Service."""
from __future__ import annotations
import logging

logger = logging.getLogger("ussd.analytics")

class USSDAnalyticsService:
    @staticmethod
    async def track_event(event_type: str, user_id: str, details: dict) -> None:
        logger.info(f"Event: {event_type}", extra={"user_id": user_id, "details": details})
    
    @staticmethod
    async def track_session_start(session_id: str, phone: str, provider: str) -> None:
        logger.info("Session start", extra={"session_id": session_id, "phone": phone[-4:], "provider": provider})
    
    @staticmethod
    async def track_session_end(session_id: str, duration_ms: int) -> None:
        logger.info("Session end", extra={"session_id": session_id, "duration_ms": duration_ms})

ussd_analytics = USSDAnalyticsService()
