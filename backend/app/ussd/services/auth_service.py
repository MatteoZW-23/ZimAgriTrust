"""USSD Auth Service."""
from __future__ import annotations
from typing import Any, Optional
from app.core.security import verify_password, get_password_hash

class USSDAuthService:
    @staticmethod
    async def verify_pin(user: Any, pin: str) -> bool:
        if not user or not user.ussd_pin_hash:
            return False
        return verify_password(pin, user.ussd_pin_hash)
    
    @staticmethod
    async def set_pin(user: Any, pin: str) -> None:
        user.ussd_pin_hash = get_password_hash(pin)
    
    @staticmethod
    async def check_lockout(user: Any) -> bool:
        return False
    
    @staticmethod
    async def record_failed_attempt(user: Any) -> int:
        return 0

ussd_auth = USSDAuthService()
