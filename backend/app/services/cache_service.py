import json
import time

from redis import asyncio as redis_async

from app.core.config import settings


class InMemoryRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.expirations: dict[str, float] = {}

    def _purge_if_expired(self, key: str) -> None:
        expires_at = self.expirations.get(key)
        if expires_at is not None and time.time() >= expires_at:
            self.store.pop(key, None)
            self.expirations.pop(key, None)

    async def get(self, key: str) -> str | None:
        self._purge_if_expired(key)
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value
        if ex is not None:
            self.expirations[key] = time.time() + ex
        else:
            self.expirations.pop(key, None)

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)
        self.expirations.pop(key, None)

    async def incr(self, key: str) -> int:
        self._purge_if_expired(key)
        current = int(self.store.get(key, "0")) + 1
        self.store[key] = str(current)
        return current

    async def expire(self, key: str, seconds: int) -> None:
        if key in self.store:
            self.expirations[key] = time.time() + seconds


_client: redis_async.Redis | InMemoryRedis | None = None


async def get_cache_client() -> redis_async.Redis | InMemoryRedis:
    global _client
    if _client is not None:
        return _client

    try:
        client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        _client = client
    except Exception:
        _client = InMemoryRedis()
    return _client


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
    raw_value = await client.get(key)
    return int(raw_value) if raw_value else 0


async def increment_counter(key: str, ttl_seconds: int) -> int:
    client = await get_cache_client()
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, ttl_seconds)
    return count
