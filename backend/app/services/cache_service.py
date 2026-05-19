"""
Production-grade cache service backed by Redis async client.
Provides atomic increment via Lua script, JSON helpers, and a sync
client for contexts that cannot use async (e.g. Alembic hooks, sync deps).

InMemoryRedis is intentionally NOT used as a silent fallback for rate
limiting or counters — callers that depend on distributed correctness
must treat a Redis connection failure as a hard error.
"""
from __future__ import annotations

import json
import time
import logging
from typing import Optional

import redis as redis_sync
from redis import asyncio as redis_async

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lua script: atomic INCR + conditional EXPIRE (set TTL only on first call)
# Returns the new counter value as an integer.
# ---------------------------------------------------------------------------
_INCR_WITH_TTL_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

# ---------------------------------------------------------------------------
# Async client (module-level singleton)
# ---------------------------------------------------------------------------
_async_client: Optional[redis_async.Redis] = None
_incr_script: Optional[redis_async.client.Script] = None  # type: ignore[type-arg]


async def get_cache_client() -> redis_async.Redis:
    global _async_client, _incr_script
    if _async_client is not None:
        return _async_client
    client: redis_async.Redis = redis_async.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    await client.ping()
    _incr_script = client.register_script(_INCR_WITH_TTL_SCRIPT)
    _async_client = client
    return _async_client


# ---------------------------------------------------------------------------
# Sync client (used only in sync contexts; never for rate limiting)
# ---------------------------------------------------------------------------
_sync_client: Optional[redis_sync.Redis] = None


def get_sync_client() -> redis_sync.Redis:
    global _sync_client
    if _sync_client is not None:
        return _sync_client
    _sync_client = redis_sync.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    _sync_client.ping()
    return _sync_client


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

async def get_json(key: str) -> dict | None:
    client = await get_cache_client()
    data = await client.get(key)
    if not data:
        return None
    return json.loads(data)


async def set_json(key: str, value: dict, ttl_seconds: int = 300) -> None:
    client = await get_cache_client()
    await client.set(key, json.dumps(value), ex=ttl_seconds)


async def delete_key(key: str) -> None:
    client = await get_cache_client()
    await client.delete(key)


async def get_counter(key: str) -> int:
    client = await get_cache_client()
    raw = await client.get(key)
    return int(raw) if raw else 0


async def increment_counter(key: str, ttl_seconds: int) -> int:
    """Atomically increment *key* and set TTL on first write via Lua script."""
    global _incr_script
    client = await get_cache_client()
    if _incr_script is None:
        _incr_script = client.register_script(_INCR_WITH_TTL_SCRIPT)
    result = await _incr_script(keys=[key], args=[str(ttl_seconds)])
    return int(result)


# ---------------------------------------------------------------------------
# CacheService class (convenience wrapper)
# ---------------------------------------------------------------------------

class CacheService:
    """Thin async wrapper. Use module-level helpers for counters."""

    async def get(self, key: str) -> str | None:
        client = await get_cache_client()
        return await client.get(key)

    async def set(self, key: str, value: str, expire: int | None = None, nx: bool = False) -> bool:
        """
        Set a Redis key. Returns True if key was set, False if nx=True and key already existed.
        nx=True implements atomic SET NX (set only if not exists) for distributed locking.
        """
        client = await get_cache_client()
        result = await client.set(key, value, ex=expire, nx=nx if nx else None)
        return result is not None

    async def delete(self, key: str) -> None:
        client = await get_cache_client()
        await client.delete(key)

    async def increment_counter(self, key: str, ttl_seconds: int) -> int:
        return await increment_counter(key, ttl_seconds)

    async def get_counter(self, key: str) -> int:
        return await get_counter(key)

    def set_sync(self, key: str, value: str, expire: int | None = None, nx: bool = False) -> bool:
        """Synchronous set — backed by a real sync Redis connection."""
        client = get_sync_client()
        return bool(client.set(key, value, ex=expire, nx=nx))

    def get_sync(self, key: str) -> str | None:
        """Synchronous get — backed by a real sync Redis connection."""
        client = get_sync_client()
        return client.get(key)

    def delete_sync(self, key: str) -> None:
        """Synchronous delete — backed by a real sync Redis connection."""
        client = get_sync_client()
        client.delete(key)


cache_service = CacheService()
