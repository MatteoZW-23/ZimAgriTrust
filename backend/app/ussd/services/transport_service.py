"""USSD Transport Service."""
from __future__ import annotations
from typing import Any, List

class USSDTransportService:
    @staticmethod
    async def get_available_drivers(db: Any, province: str) -> List[Any]:
        return []
    
    @staticmethod
    async def request_transport(db: Any, user_id: str, pickup: str, dropoff: str) -> Any:
        return None

ussd_transport = USSDTransportService()
