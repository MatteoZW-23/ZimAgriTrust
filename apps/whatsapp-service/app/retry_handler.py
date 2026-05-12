"""Retry handler for Redis Streams with exponential backoff."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.redis_client import RedisConsumer
from app.whatsapp_bridge import WhatsAppBridgeClient
from app.config import settings

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retry logic for failed message processing."""

    def __init__(
        self,
        consumer: RedisConsumer,
        bridge: WhatsAppBridgeClient,
    ):
        self._consumer = consumer
        self._bridge = bridge
        self._max_retries = 3
        self._base_delay = 1.0  # seconds
        self._max_delay = 60.0  # seconds

    async def process_with_retry(
        self,
        stream_name: str,
        message_id: str,
        phone: str,
        message: str,
    ) -> bool:
        """Process message with retry logic."""
        retry_count = 0
        delay = self._base_delay

        while retry_count < self._max_retries:
            try:
                success = await self._bridge.send_message(phone, message)
                if success:
                    await self._consumer.acknowledge_message(stream_name, message_id)
                    logger.info(f"Message {message_id} delivered successfully on attempt {retry_count + 1}")
                    return True
                else:
                    retry_count += 1
                    if retry_count < self._max_retries:
                        delay = min(delay * 2, self._max_delay)
                        logger.warning(
                            f"Message {message_id} failed, retry {retry_count}/{self._max_retries} in {delay}s"
                        )
                        await asyncio.sleep(delay)

            except Exception as e:
                retry_count += 1
                if retry_count < self._max_retries:
                    delay = min(delay * 2, self._max_delay)
                    logger.error(
                        f"Error processing message {message_id}: {e}, "
                        f"retry {retry_count}/{self._max_retries} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for message {message_id}: {e}")
                    # Move to dead-letter queue or log for manual review
                    return False

        # Max retries exceeded - move to dead-letter stream
        await self._move_to_dead_letter(stream_name, message_id, phone, message)
        return False

    async def _move_to_dead_letter(
        self,
        stream_name: str,
        message_id: str,
        phone: str,
        message: str,
    ) -> None:
        """Move failed message to dead-letter queue."""
        try:
            dead_letter_stream = f"{stream_name}:dead_letter"
            import json
            from datetime import datetime, timezone

            dead_letter_data = {
                "original_stream": stream_name,
                "original_message_id": message_id,
                "phone": phone,
                "message": message,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error_reason": "max_retries_exceeded",
            }

            await self._consumer._redis.xadd(dead_letter_stream, dead_letter_data)
            await self._consumer.acknowledge_message(stream_name, message_id)
            logger.warning(f"Message {message_id} moved to dead-letter queue")
        except Exception as e:
            logger.error(f"Failed to move message to dead-letter queue: {e}")


class CircuitBreaker:
    """Circuit breaker pattern for WhatsApp Bridge failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call."""
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            self._failure_count = 0
            logger.info("Circuit breaker reset to CLOSED")

    def _on_failure(self):
        """Handle failed call."""
        import time
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self._last_failure_time is None:
            return False
        import time
        return (time.time() - self._last_failure_time) > self._recovery_timeout

    def get_state(self) -> dict:
        """Get circuit breaker state for monitoring."""
        import time
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time,
            "time_since_last_failure": (
                time.time() - self._last_failure_time
                if self._last_failure_time
                else None
            ),
        }
