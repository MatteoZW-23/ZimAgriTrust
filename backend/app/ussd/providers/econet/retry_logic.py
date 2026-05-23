"""
Econet Retry Logic
==================
Handles Econet-specific retry behavior.
Econet retries callbacks aggressively when responses are slow.
"""
from __future__ import annotations

import time
import logging
from typing import Optional

from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("ussd.provider.econet.retry")

ECONET_RETRY_PREFIX = "ussd:econet:retry:"
ECONET_TIMEOUT_SECONDS = 25  # Econet times out after ~25-30s
ECONET_MAX_RETRIES = 3


class EconetRetryLogic:
    """Handles Econet retry storm protection."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        return self._client

    async def is_duplicate_callback(self, session_id: str, text: str) -> bool:
        """
        Check if this is a duplicate Econet callback.
        Econet resends after ~5s if no response.
        """
        client = await self._get_client()
        key = f"{ECONET_RETRY_PREFIX}{session_id}:{hash(text)}"
        exists = await client.exists(key)
        if exists:
            logger.info(
                "Econet duplicate callback detected",
                extra={"session_id": session_id},
            )
            return True
        # Mark as seen for 30 seconds
        await client.set(key, "1", ex=30)
        return False

    async def get_retry_count(self, session_id: str) -> int:
        """Get current retry count for session."""
        client = await self._get_client()
        key = f"{ECONET_RETRY_PREFIX}{session_id}:count"
        count = await client.get(key)
        return int(count) if count else 0

    async def increment_retry(self, session_id: str) -> int:
        """Increment retry count. Returns new count."""
        client = await self._get_client()
        key = f"{ECONET_RETRY_PREFIX}{session_id}:count"
        pipe = client.pipeline(transaction=True)
        pipe.incr(key)
        pipe.expire(key, ECONET_TIMEOUT_SECONDS * 2)
        results = await pipe.execute()
        return results[0]

    async def should_process(self, session_id: str, text: str) -> bool:
        """Determine if this request should be processed or is a retry."""
        is_dup = await self.is_duplicate_callback(session_id, text)
        if is_dup:
            return False
        retry_count = await self.get_retry_count(session_id)
        if retry_count >= ECONET_MAX_RETRIES:
            logger.warning(
                "Econet max retries exceeded",
                extra={"session_id": session_id, "retries": retry_count},
            )
            return False
        await self.increment_retry(session_id)
        return True


econet_retry = EconetRetryLogic()
