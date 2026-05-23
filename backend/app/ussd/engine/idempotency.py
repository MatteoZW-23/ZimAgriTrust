"""
USSD Idempotency Engine
========================
Ensures duplicate telco callbacks return the same response.
Zimbabwe networks frequently retry requests due to:
- Network timeouts
- Provider retries
- Mobile retry storms
- Duplicate callbacks

Uses Redis with short TTL to deduplicate within the retry window.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional

from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("ussd.idempotency")

IDEMPOTENCY_PREFIX = "ussd:idem:"
DEFAULT_TTL = 60  # 60 seconds dedup window
MAX_TTL = 300  # 5 minutes absolute max


class IdempotencyEngine:
    """
    Distributed idempotency for USSD requests.
    Keyed on session_id + input hash to handle duplicate callbacks.
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                retry_on_timeout=True,
            )
        return self._client

    def _compute_key(self, session_id: str, text: str, phone: str) -> str:
        """Compute deterministic idempotency key."""
        payload = f"{session_id}|{text}|{phone}"
        digest = hashlib.sha256(payload.encode()).hexdigest()[:24]
        return f"{IDEMPOTENCY_PREFIX}{digest}"

    async def check(self, session_id: str, text: str, phone: str) -> Optional[dict]:
        """
        Check if this exact request has been processed before.
        Returns cached response dict or None.
        """
        client = await self._get_client()
        key = self._compute_key(session_id, text, phone)
        cached = await client.get(key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info(
                    "Idempotent hit",
                    extra={
                        "session_id": session_id,
                        "key": key[-12:],
                        "age_ms": int((time.time() - data.get("ts", 0)) * 1000),
                    },
                )
                return data.get("response")
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    async def store(
        self,
        session_id: str,
        text: str,
        phone: str,
        response: dict,
        ttl: int = DEFAULT_TTL,
    ) -> None:
        """Store response for future duplicate detection."""
        client = await self._get_client()
        key = self._compute_key(session_id, text, phone)
        payload = json.dumps({"response": response, "ts": time.time()})
        await client.set(key, payload, ex=min(ttl, MAX_TTL))

    async def invalidate(self, session_id: str, text: str, phone: str) -> None:
        """Invalidate cached response (e.g., after session state change)."""
        client = await self._get_client()
        key = self._compute_key(session_id, text, phone)
        await client.delete(key)

    async def get_stats(self) -> dict:
        """Get idempotency cache statistics."""
        client = await self._get_client()
        cursor = 0
        count = 0
        while True:
            cursor, keys = await client.scan(cursor, match=f"{IDEMPOTENCY_PREFIX}*", count=100)
            count += len(keys)
            if cursor == 0:
                break
        return {"cached_responses": count}


# Module-level singleton
idempotency_engine = IdempotencyEngine()
