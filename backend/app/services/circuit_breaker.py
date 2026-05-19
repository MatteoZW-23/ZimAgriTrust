"""
Circuit Breaker Pattern for Payment Provider Resilience

Prevents cascading failures and provides fallback when providers are down.
Implements state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
"""
import time
import logging
from enum import Enum
from typing import Optional, Callable, Any, TypeVar
from functools import wraps
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation, requests pass through
    OPEN = "OPEN"          # Circuit is open, requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if provider has recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with configurable thresholds.
    Uses Redis for distributed state across multiple instances.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: Exception = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Seconds to stay open before attempting recovery
        self.expected_exception = expected_exception

    def _get_state_key(self) -> str:
        return f"circuit_breaker:{self.name}:state"

    def _get_failure_count_key(self) -> str:
        return f"circuit_breaker:{self.name}:failures"

    def _get_last_failure_time_key(self) -> str:
        return f"circuit_breaker:{self.name}:last_failure"

    async def get_state(self) -> CircuitState:
        """Get current circuit state from Redis"""
        state_str = await cache_service.get(self._get_state_key())
        if not state_str:
            return CircuitState.CLOSED
        
        state = CircuitState(state_str)
        
        # Auto-transition from OPEN to HALF_OPEN after timeout
        if state == CircuitState.OPEN:
            last_failure_str = await cache_service.get(self._get_last_failure_time_key())
            if last_failure_str:
                last_failure = datetime.fromisoformat(last_failure_str)
                if datetime.utcnow() - last_failure > timedelta(seconds=self.timeout):
                    await self.set_state(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")
                    return CircuitState.HALF_OPEN
        
        return state

    async def set_state(self, state: CircuitState) -> None:
        """Set circuit state in Redis"""
        await cache_service.set(self._get_state_key(), state.value, expire=86400)  # 24h TTL

    async def get_failure_count(self) -> int:
        """Get current failure count"""
        count = await cache_service.get(self._get_failure_count_key())
        return int(count) if count else 0

    async def increment_failure_count(self) -> int:
        """Increment failure count and return new count"""
        count = await cache_service.increment_counter(self._get_failure_count_key(), window=3600)
        return count

    async def reset_failure_count(self) -> None:
        """Reset failure count to 0"""
        await cache_service.delete(self._get_failure_count_key())

    async def record_failure(self) -> None:
        """Record a failure and potentially open the circuit"""
        count = await self.increment_failure_count()
        await cache_service.set(
            self._get_last_failure_time_key(),
            datetime.utcnow().isoformat(),
            expire=3600
        )
        
        logger.warning(f"Circuit breaker {self.name} failure count: {count}/{self.failure_threshold}")
        
        if count >= self.failure_threshold:
            await self.set_state(CircuitState.OPEN)
            logger.error(f"Circuit breaker {self.name} opened due to {count} failures")

    async def record_success(self) -> None:
        """Record a success and potentially close the circuit"""
        state = await self.get_state()
        
        if state == CircuitState.HALF_OPEN:
            await self.set_state(CircuitState.CLOSED)
            await self.reset_failure_count()
            logger.info(f"Circuit breaker {self.name} closed after successful test")
        elif state == CircuitState.CLOSED:
            await self.reset_failure_count()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        Raises CircuitBreakerError if circuit is open.
        """
        state = await self.get_state()
        
        if state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker {self.name} is OPEN, rejecting request")
            raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
        
        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except self.expected_exception as e:
            await self.record_failure()
            raise
        except Exception as e:
            # Unexpected exceptions don't count as circuit breaker failures
            logger.error(f"Unexpected error in circuit breaker {self.name}: {e}")
            raise


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: Exception = Exception,
):
    """
    Decorator for circuit breaker protection.
    """
    breaker = CircuitBreaker(name, failure_threshold, timeout, expected_exception)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured circuit breakers for common providers
ECOCASH_BREAKER = CircuitBreaker("ecocash", failure_threshold=5, timeout=60)
ONEMONEY_BREAKER = CircuitBreaker("onemoney", failure_threshold=5, timeout=60)
ZIPIT_BREAKER = CircuitBreaker("zipit", failure_threshold=3, timeout=120)
WALLET_BREAKER = CircuitBreaker("wallet", failure_threshold=10, timeout=30)
