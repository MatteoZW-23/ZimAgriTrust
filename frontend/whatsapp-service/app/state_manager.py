"""Redis-based state management for WhatsApp conversational flows."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class StateManager:
    """Manages conversational state using Redis."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._state_prefix = "wa_state:"
        self._state_ttl = 3600  # 1 hour

    async def get_state(self, phone: str) -> Dict[str, Any]:
        """Get user's conversational state."""
        key = f"{self._state_prefix}{phone}"
        try:
            state = await self._redis.get(key)
            if state:
                return json.loads(state)
            return {"flow": "IDLE", "data": {}}
        except Exception as e:
            logger.error(f"Error getting state for {phone}: {e}")
            return {"flow": "IDLE", "data": {}}

    async def set_state(
        self,
        phone: str,
        flow: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set user's conversational state."""
        key = f"{self._state_prefix}{phone}"
        state = {"flow": flow, "data": data or {}}
        try:
            await self._redis.setex(
                key,
                self._state_ttl,
                json.dumps(state),
            )
            logger.debug(f"Set state for {phone}: flow={flow}")
        except Exception as e:
            logger.error(f"Error setting state for {phone}: {e}")

    async def clear_state(self, phone: str) -> None:
        """Clear user's conversational state."""
        key = f"{self._state_prefix}{phone}"
        try:
            await self._redis.delete(key)
            logger.debug(f"Cleared state for {phone}")
        except Exception as e:
            logger.error(f"Error clearing state for {phone}: {e}")

    async def update_state_data(
        self,
        phone: str,
        data_update: Dict[str, Any],
    ) -> None:
        """Update user's state data without changing the flow."""
        state = await self.get_state(phone)
        state["data"].update(data_update)
        await self.set_state(phone, state["flow"], state["data"])

    async def get_flow(self, phone: str) -> str:
        """Get user's current flow."""
        state = await self.get_state(phone)
        return state.get("flow", "IDLE")

    async def set_idle(self, phone: str) -> None:
        """Set user to idle state."""
        await self.set_state(phone, "IDLE", {})
