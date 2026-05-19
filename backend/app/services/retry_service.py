"""
Exponential Backoff Retry with Dead-Letter Queue

Implements resilient retry logic for external provider calls.
Failed operations are retried with exponential backoff before moving to DLQ.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Callable, TypeVar, Any
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStatus(str, Enum):
    """Status of retry attempts"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class RetryConfig:
    """Configuration for retry logic"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_attempts = max_attempts
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier


class RetryService:
    """
    Retry service with exponential backoff and dead-letter queue.
    Uses Redis for distributed retry state.
    """

    @staticmethod
    def calculate_backoff(attempt: int, config: RetryConfig) -> float:
        """
        Calculate exponential backoff delay.
        delay = min(initial_backoff * (multiplier ^ (attempt - 1)), max_backoff)
        """
        delay = config.initial_backoff * (config.backoff_multiplier ** (attempt - 1))
        return min(delay, config.max_backoff)

    @staticmethod
    async def execute_with_retry(
        func: Callable[..., Any],
        config: RetryConfig = None,
        operation_name: str = "operation",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry.
        """
        if config is None:
            config = RetryConfig()

        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{config.max_attempts}: {e}"
                )
                
                if attempt < config.max_attempts:
                    backoff = RetryService.calculate_backoff(attempt, config)
                    logger.info(f"Retrying {operation_name} in {backoff:.2f}s")
                    await asyncio.sleep(backoff)
        
        # All attempts failed
        logger.error(
            f"{operation_name} failed after {config.max_attempts} attempts"
        )
        raise last_exception

    @staticmethod
    async def schedule_retry(
        operation_id: str,
        func: Callable[..., Any],
        config: RetryConfig = None,
        attempt: int = 1,
        *args,
        **kwargs
    ) -> None:
        """
        Schedule a retry operation for background execution.
        """
        if config is None:
            config = RetryConfig()

        retry_key = f"retry:{operation_id}"
        
        # Store retry metadata
        await cache_service.set(
            f"{retry_key}:attempt",
            attempt,
            expire=86400
        )
        await cache_service.set(
            f"{retry_key}:scheduled_at",
            datetime.utcnow().isoformat(),
            expire=86400
        )
        
        # Calculate delay and schedule
        backoff = RetryService.calculate_backoff(attempt, config)
        await asyncio.sleep(backoff)
        
        try:
            result = await func(*args, **kwargs)
            await cache_service.delete(f"{retry_key}:attempt")
            await cache_service.delete(f"{retry_key}:scheduled_at")
            return result
        except Exception as e:
            if attempt >= config.max_attempts:
                # Move to dead-letter queue
                await RetryService.move_to_dead_letter(
                    operation_id,
                    str(e),
                    attempt
                )
                raise
            else:
                # Schedule next retry
                await RetryService.schedule_retry(
                    operation_id,
                    func,
                    config,
                    attempt + 1,
                    *args,
                    **kwargs
                )
                raise

    @staticmethod
    async def move_to_dead_letter(
        operation_id: str,
        error_message: str,
        attempt_count: int
    ) -> None:
        """
        Move failed operation to dead-letter queue for manual inspection.
        """
        dlq_key = f"dead_letter_queue:{operation_id}"
        
        dlq_entry = {
            "operation_id": operation_id,
            "error_message": error_message,
            "attempt_count": attempt_count,
            "failed_at": datetime.utcnow().isoformat(),
            "status": RetryStatus.DEAD_LETTER.value
        }
        
        await cache_service.set(dlq_key, str(dlq_entry), expire=604800)  # 7 days
        logger.error(f"Operation {operation_id} moved to dead-letter queue: {error_message}")

    @staticmethod
    async def get_dead_letter_entries(limit: int = 100) -> list:
        """
        Get entries from dead-letter queue.
        """
        # In production, this would query a proper DLQ table or Redis sorted set
        # For now, return empty list as placeholder
        return []

    @staticmethod
    async def retry_dead_letter_entry(operation_id: str) -> bool:
        """
        Retry a dead-letter queue entry.
        """
        dlq_key = f"dead_letter_queue:{operation_id}"
        entry = await cache_service.get(dlq_key)
        
        if not entry:
            return False
        
        await cache_service.delete(dlq_key)
        # In production, this would re-execute the operation
        logger.info(f"Retrying dead-letter entry: {operation_id}")
        return True


# Default retry configurations
DEFAULT_RETRY = RetryConfig(max_attempts=3, initial_backoff=1.0, max_backoff=60.0)
AGGRESSIVE_RETRY = RetryConfig(max_attempts=5, initial_backoff=0.5, max_backoff=30.0)
CONSERVATIVE_RETRY = RetryConfig(max_attempts=2, initial_backoff=2.0, max_backoff=120.0)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    backoff_multiplier: float = 2.0,
):
    """
    Decorator for retry with exponential backoff.
    """
    config = RetryConfig(max_attempts, initial_backoff, max_backoff, backoff_multiplier)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await RetryService.execute_with_retry(
                func,
                config,
                func.__name__,
                *args,
                **kwargs
            )
        return wrapper
    return decorator
