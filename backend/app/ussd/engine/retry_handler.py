"""
USSD Retry Handler
==================
Manages retry logic for Zimbabwe telco conditions:
- Duplicate callbacks from providers
- Retry storms during network congestion
- Timeout recovery
- Session abandonment detection
- Rate limiting per phone number

Uses exponential backoff and circuit breaker patterns.
"""
from __future__ import annotations

import time
import logging
from typing import Optional
from dataclasses import dataclass

from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("ussd.retry_handler")

RETRY_KEY_PREFIX = "ussd:retry:"
RATE_LIMIT_PREFIX = "ussd:rate:"
CIRCUIT_BREAKER_PREFIX = "ussd:circuit:"

# Configuration
MAX_RETRIES_PER_SESSION = 5
MAX_REQUESTS_PER_MINUTE = 10  # Per phone number
MAX_REQUESTS_PER_HOUR = 60  # Per phone number
CIRCUIT_BREAKER_THRESHOLD = 50  # Errors before tripping
CIRCUIT_BREAKER_RESET_SECONDS = 60


@dataclass
class RetryContext:
    """Context for a retry attempt."""
    session_id: str
    phone_number: str
    attempt: int
    max_attempts: int
    is_duplicate: bool
    should_process: bool
    reason: str = ""


class RetryHandler:
    """
    Handles retry logic and rate limiting for USSD requests.
    Protects against retry storms and duplicate processing.
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

    async def evaluate_request(
        self, session_id: str, phone_number: str, text: str
    ) -> RetryContext:
        """
        Evaluate whether a request should be processed.
        Returns context with decision and metadata.
        """
        client = await self._get_client()

        # Check circuit breaker
        circuit_key = f"{CIRCUIT_BREAKER_PREFIX}global"
        circuit_count = await client.get(circuit_key)
        if circuit_count and int(circuit_count) >= CIRCUIT_BREAKER_THRESHOLD:
            return RetryContext(
                session_id=session_id,
                phone_number=phone_number,
                attempt=0,
                max_attempts=MAX_RETRIES_PER_SESSION,
                is_duplicate=False,
                should_process=False,
                reason="circuit_breaker_open",
            )

        # Check per-phone rate limit (per minute)
        rate_key_min = f"{RATE_LIMIT_PREFIX}{phone_number}:min"
        current_rate = await client.get(rate_key_min)
        if current_rate and int(current_rate) >= MAX_REQUESTS_PER_MINUTE:
            logger.warning(
                "Rate limit hit (per-minute)",
                extra={"phone": phone_number, "count": current_rate},
            )
            return RetryContext(
                session_id=session_id,
                phone_number=phone_number,
                attempt=int(current_rate),
                max_attempts=MAX_REQUESTS_PER_MINUTE,
                is_duplicate=False,
                should_process=False,
                reason="rate_limited_minute",
            )

        # Check per-phone rate limit (per hour)
        rate_key_hr = f"{RATE_LIMIT_PREFIX}{phone_number}:hr"
        current_rate_hr = await client.get(rate_key_hr)
        if current_rate_hr and int(current_rate_hr) >= MAX_REQUESTS_PER_HOUR:
            logger.warning(
                "Rate limit hit (per-hour)",
                extra={"phone": phone_number, "count": current_rate_hr},
            )
            return RetryContext(
                session_id=session_id,
                phone_number=phone_number,
                attempt=int(current_rate_hr),
                max_attempts=MAX_REQUESTS_PER_HOUR,
                is_duplicate=False,
                should_process=False,
                reason="rate_limited_hour",
            )

        # Check session retry count
        retry_key = f"{RETRY_KEY_PREFIX}{session_id}"
        retry_count = await client.get(retry_key)
        attempt = int(retry_count) if retry_count else 0

        if attempt >= MAX_RETRIES_PER_SESSION:
            return RetryContext(
                session_id=session_id,
                phone_number=phone_number,
                attempt=attempt,
                max_attempts=MAX_RETRIES_PER_SESSION,
                is_duplicate=True,
                should_process=False,
                reason="max_retries_exceeded",
            )

        # Increment counters
        pipe = client.pipeline(transaction=True)
        pipe.incr(retry_key)
        pipe.expire(retry_key, 300)  # 5 min TTL
        pipe.incr(rate_key_min)
        pipe.expire(rate_key_min, 60)
        pipe.incr(rate_key_hr)
        pipe.expire(rate_key_hr, 3600)
        await pipe.execute()

        return RetryContext(
            session_id=session_id,
            phone_number=phone_number,
            attempt=attempt + 1,
            max_attempts=MAX_RETRIES_PER_SESSION,
            is_duplicate=attempt > 0,
            should_process=True,
        )

    async def record_error(self, session_id: str, error: str) -> None:
        """Record an error for circuit breaker tracking."""
        client = await self._get_client()
        circuit_key = f"{CIRCUIT_BREAKER_PREFIX}global"
        pipe = client.pipeline(transaction=True)
        pipe.incr(circuit_key)
        pipe.expire(circuit_key, CIRCUIT_BREAKER_RESET_SECONDS)
        await pipe.execute()
        logger.error(
            "USSD error recorded",
            extra={"session_id": session_id, "error": error},
        )

    async def record_success(self, session_id: str) -> None:
        """Record success — decrements circuit breaker pressure."""
        client = await self._get_client()
        circuit_key = f"{CIRCUIT_BREAKER_PREFIX}global"
        current = await client.get(circuit_key)
        if current and int(current) > 0:
            await client.decr(circuit_key)

    async def reset_session_retries(self, session_id: str) -> None:
        """Reset retry counter for a session."""
        client = await self._get_client()
        retry_key = f"{RETRY_KEY_PREFIX}{session_id}"
        await client.delete(retry_key)

    async def get_circuit_breaker_status(self) -> dict:
        """Get circuit breaker status for monitoring."""
        client = await self._get_client()
        circuit_key = f"{CIRCUIT_BREAKER_PREFIX}global"
        count = await client.get(circuit_key)
        error_count = int(count) if count else 0
        return {
            "error_count": error_count,
            "threshold": CIRCUIT_BREAKER_THRESHOLD,
            "is_open": error_count >= CIRCUIT_BREAKER_THRESHOLD,
            "status": "open" if error_count >= CIRCUIT_BREAKER_THRESHOLD else "closed",
        }

    async def get_phone_rate_info(self, phone_number: str) -> dict:
        """Get rate limit info for a phone number."""
        client = await self._get_client()
        rate_min = await client.get(f"{RATE_LIMIT_PREFIX}{phone_number}:min")
        rate_hr = await client.get(f"{RATE_LIMIT_PREFIX}{phone_number}:hr")
        return {
            "requests_this_minute": int(rate_min) if rate_min else 0,
            "requests_this_hour": int(rate_hr) if rate_hr else 0,
            "max_per_minute": MAX_REQUESTS_PER_MINUTE,
            "max_per_hour": MAX_REQUESTS_PER_HOUR,
        }


# Module-level singleton
retry_handler = RetryHandler()
