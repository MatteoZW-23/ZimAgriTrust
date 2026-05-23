"""Telecel Retry Logic — handles Telecel-specific retry behavior."""
from __future__ import annotations

import logging
from typing import Optional

from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("ussd.provider.telecel.retry")

TELECEL_RETRY_PREFIX = "ussd:telecel:retry:"
TELECEL_MAX_RETRIES = 2


class TelecelRetryLogic:
    """Handles Telecel retry protection."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True,
                socket_connect_timeout=2, socket_timeout=2,
            )
        return self._client

    async def is_duplicate_callback(self, session_id: str, text: str) -> bool:
        """Check for duplicate Telecel callback."""
        client = await self._get_client()
        key = f"{TELECEL_RETRY_PREFIX}{session_id}:{hash(text)}"
        exists = await client.exists(key)
        if exists:
            logger.info("Telecel duplicate detected", extra={"session_id": session_id})
            return True
        await client.set(key, "1", ex=20)
        return False

    async def should_process(self, session_id: str, text: str) -> bool:
        """Determine if request should be processed."""
        return not await self.is_duplicate_callback(session_id, text)


telecel_retry = TelecelRetryLogic()
