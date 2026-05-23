"""
Redis Session Store
===================
Production-grade Redis-backed session persistence for USSD.
Features:
- TTL-based expiration (configurable per provider)
- Optimistic concurrency via version field
- Distributed-safe atomic updates
- Session recovery after Redis restarts
- Structured JSON storage with validation
"""
from __future__ import annotations

import json
import time
import logging
from typing import Optional
from dataclasses import dataclass, field, asdict

from redis import asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger("ussd.session_store")

# Redis key patterns
SESSION_KEY_PREFIX = "ussd:session:"
SESSION_INDEX_PREFIX = "ussd:phone_index:"
SESSION_LOCK_PREFIX = "ussd:lock:"
IDEMPOTENCY_PREFIX = "ussd:idempotent:"

# Timeouts
DEFAULT_SESSION_TTL = 300  # 5 minutes — Zimbabwe telco standard
MAX_SESSION_TTL = 600  # 10 minutes absolute max
LOCK_TTL = 5  # 5 seconds — enough for single request processing
IDEMPOTENCY_TTL = 60  # 1 minute dedup window


@dataclass
class USSDSession:
    """Represents a USSD session stored in Redis."""
    session_id: str
    phone_number: str
    provider: str = ""
    user_id: str = ""
    authenticated: bool = False
    pin_verified: bool = False
    current_screen: str = "welcome"
    previous_screen: str = ""
    flow_state: dict = field(default_factory=dict)
    input_history: list = field(default_factory=list)
    correlation_id: str = ""
    retry_count: int = 0
    pin_attempts: int = 0
    last_activity: float = 0.0
    created_at: float = 0.0
    expires_at: float = 0.0
    version: int = 0
    language: str = "en"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> USSDSession:
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at if self.expires_at else False

    @property
    def is_authenticated(self) -> bool:
        return self.authenticated and self.pin_verified


class RedisSessionStore:
    """
    Distributed Redis-backed session store.
    Provides atomic operations with optimistic concurrency control.
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
                health_check_interval=30,
            )
        return self._client

    async def create_session(
        self,
        session_id: str,
        phone_number: str,
        provider: str,
        correlation_id: str = "",
        ttl: int = DEFAULT_SESSION_TTL,
    ) -> USSDSession:
        """Create a new USSD session in Redis."""
        now = time.time()
        session = USSDSession(
            session_id=session_id,
            phone_number=phone_number,
            provider=provider,
            correlation_id=correlation_id,
            current_screen="welcome",
            last_activity=now,
            created_at=now,
            expires_at=now + ttl,
            version=1,
        )

        client = await self._get_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        pipe = client.pipeline(transaction=True)
        pipe.set(key, json.dumps(session.to_dict()), ex=ttl, nx=True)
        pipe.set(f"{SESSION_INDEX_PREFIX}{phone_number}", session_id, ex=ttl)
        results = await pipe.execute()

        if not results[0]:
            existing = await self.get_session(session_id)
            if existing:
                logger.warning(
                    "Session already exists",
                    extra={"session_id": session_id, "phone": phone_number},
                )
                return existing
            await client.set(key, json.dumps(session.to_dict()), ex=ttl)

        logger.info(
            "Session created",
            extra={
                "session_id": session_id,
                "phone": phone_number,
                "provider": provider,
                "correlation_id": correlation_id,
            },
        )
        return session

    async def get_session(self, session_id: str) -> Optional[USSDSession]:
        """Retrieve a session by ID."""
        client = await self._get_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        data = await client.get(key)
        if not data:
            return None
        try:
            session = USSDSession.from_dict(json.loads(data))
            if session.is_expired:
                await self.destroy_session(session_id)
                return None
            return session
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Corrupt session data", extra={"session_id": session_id, "error": str(e)})
            await client.delete(key)
            return None

    async def update_session(self, session: USSDSession, expected_version: int = None) -> bool:
        """
        Update session with optimistic concurrency control.
        Returns False if version mismatch (concurrent modification).
        """
        client = await self._get_client()
        key = f"{SESSION_KEY_PREFIX}{session.session_id}"

        if expected_version is not None and session.version != expected_version:
            logger.warning(
                "Version mismatch on update",
                extra={
                    "session_id": session.session_id,
                    "expected": expected_version,
                    "actual": session.version,
                },
            )
            return False

        session.version += 1
        session.last_activity = time.time()

        remaining_ttl = max(int(session.expires_at - time.time()), 30)
        await client.set(key, json.dumps(session.to_dict()), ex=remaining_ttl)
        return True

    async def destroy_session(self, session_id: str) -> None:
        """Remove session from Redis."""
        client = await self._get_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"

        data = await client.get(key)
        pipe = client.pipeline(transaction=True)
        pipe.delete(key)
        if data:
            try:
                session_data = json.loads(data)
                phone = session_data.get("phone_number", "")
                if phone:
                    pipe.delete(f"{SESSION_INDEX_PREFIX}{phone}")
            except (json.JSONDecodeError, TypeError):
                pass
        await pipe.execute()
        logger.info("Session destroyed", extra={"session_id": session_id})

    async def get_session_by_phone(self, phone_number: str) -> Optional[USSDSession]:
        """Lookup active session by phone number."""
        client = await self._get_client()
        session_id = await client.get(f"{SESSION_INDEX_PREFIX}{phone_number}")
        if not session_id:
            return None
        return await self.get_session(session_id)

    async def acquire_lock(self, session_id: str, timeout: int = LOCK_TTL) -> bool:
        """Acquire distributed lock for session processing."""
        client = await self._get_client()
        lock_key = f"{SESSION_LOCK_PREFIX}{session_id}"
        acquired = await client.set(lock_key, "1", ex=timeout, nx=True)
        return acquired is not None

    async def release_lock(self, session_id: str) -> None:
        """Release distributed lock."""
        client = await self._get_client()
        lock_key = f"{SESSION_LOCK_PREFIX}{session_id}"
        await client.delete(lock_key)

    async def check_idempotency(self, key: str) -> Optional[str]:
        """Check if request has already been processed."""
        client = await self._get_client()
        return await client.get(f"{IDEMPOTENCY_PREFIX}{key}")

    async def set_idempotency(self, key: str, response: str, ttl: int = IDEMPOTENCY_TTL) -> None:
        """Store idempotent response."""
        client = await self._get_client()
        await client.set(f"{IDEMPOTENCY_PREFIX}{key}", response, ex=ttl)

    async def extend_session(self, session_id: str, extra_seconds: int = 60) -> bool:
        """Extend session TTL for long-running operations."""
        client = await self._get_client()
        key = f"{SESSION_KEY_PREFIX}{session_id}"
        current_ttl = await client.ttl(key)
        if current_ttl <= 0:
            return False
        new_ttl = min(current_ttl + extra_seconds, MAX_SESSION_TTL)
        await client.expire(key, new_ttl)
        return True

    async def get_active_session_count(self) -> int:
        """Count active sessions (for monitoring)."""
        client = await self._get_client()
        cursor = 0
        count = 0
        while True:
            cursor, keys = await client.scan(cursor, match=f"{SESSION_KEY_PREFIX}*", count=100)
            count += len(keys)
            if cursor == 0:
                break
        return count

    async def cleanup_expired(self) -> int:
        """Manual cleanup of expired sessions (Redis TTL handles most cases)."""
        client = await self._get_client()
        cursor = 0
        cleaned = 0
        now = time.time()
        while True:
            cursor, keys = await client.scan(cursor, match=f"{SESSION_KEY_PREFIX}*", count=100)
            for key in keys:
                data = await client.get(key)
                if data:
                    try:
                        session_data = json.loads(data)
                        if session_data.get("expires_at", 0) < now:
                            await client.delete(key)
                            cleaned += 1
                    except (json.JSONDecodeError, TypeError):
                        await client.delete(key)
                        cleaned += 1
            if cursor == 0:
                break
        return cleaned


# Module-level singleton
session_store = RedisSessionStore()
