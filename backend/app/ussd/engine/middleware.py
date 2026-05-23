"""
USSD Middleware
===============
Request/response middleware pipeline for USSD processing.
Applied before and after screen handlers.

Middleware chain:
1. Validation middleware — sanitize and validate input
2. Retry middleware — check duplicates and rate limits
3. Auth middleware — verify session authentication state
4. Logging middleware — structured audit logging
5. Metrics middleware — track performance and errors
"""
from __future__ import annotations

import time
import logging
from typing import Any, Callable, Awaitable
from dataclasses import dataclass

from app.ussd.engine.redis_session_store import USSDSession
from app.ussd.engine.validators import validator
from app.ussd.engine.retry_handler import retry_handler, RetryContext

logger = logging.getLogger("ussd.middleware")


@dataclass
class USSDContext:
    """Context passed through middleware chain."""
    session_id: str
    phone_number: str
    text: str
    provider: str
    correlation_id: str
    session: USSDSession | None = None
    retry_context: RetryContext | None = None
    start_time: float = 0.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.start_time == 0.0:
            self.start_time = time.time()


class MiddlewareResult:
    """Result from middleware processing."""

    def __init__(self, proceed: bool = True, response: dict = None, context: USSDContext = None):
        self.proceed = proceed
        self.response = response
        self.context = context


class ValidationMiddleware:
    """Validates and sanitizes incoming USSD requests."""

    async def process(self, ctx: USSDContext) -> MiddlewareResult:
        # Validate session ID
        if not validator.validate_session_id(ctx.session_id):
            logger.warning("Invalid session_id", extra={"session_id": ctx.session_id[:20]})
            return MiddlewareResult(
                proceed=False,
                response={"message": "END Invalid request.", "end_session": True},
            )

        # Validate phone number
        if not validator.validate_phone_number(ctx.phone_number):
            logger.warning("Invalid phone", extra={"phone": ctx.phone_number[:10]})
            return MiddlewareResult(
                proceed=False,
                response={"message": "END Invalid phone number.", "end_session": True},
            )

        # Normalize phone number
        ctx.phone_number = validator.normalize_phone_number(ctx.phone_number)

        # Sanitize text input
        ctx.text = validator.sanitize_input(ctx.text)

        # Check for blacklisted inputs
        if ctx.text and validator.is_blacklisted(ctx.text):
            return MiddlewareResult(
                proceed=False,
                response={"message": "END Invalid input.", "end_session": True},
            )

        return MiddlewareResult(proceed=True, context=ctx)


class RetryMiddleware:
    """Handles retry detection and rate limiting."""

    async def process(self, ctx: USSDContext) -> MiddlewareResult:
        retry_ctx = await retry_handler.evaluate_request(
            session_id=ctx.session_id,
            phone_number=ctx.phone_number,
            text=ctx.text,
        )
        ctx.retry_context = retry_ctx

        if not retry_ctx.should_process:
            if retry_ctx.reason == "rate_limited_minute":
                return MiddlewareResult(
                    proceed=False,
                    response={
                        "message": "END Too many requests. Wait a moment and try again.",
                        "end_session": True,
                    },
                )
            elif retry_ctx.reason == "rate_limited_hour":
                return MiddlewareResult(
                    proceed=False,
                    response={
                        "message": "END Request limit reached. Try again later.",
                        "end_session": True,
                    },
                )
            elif retry_ctx.reason == "circuit_breaker_open":
                return MiddlewareResult(
                    proceed=False,
                    response={
                        "message": "END Service temporarily unavailable. Try again shortly.",
                        "end_session": True,
                    },
                )
            elif retry_ctx.reason == "max_retries_exceeded":
                return MiddlewareResult(
                    proceed=False,
                    response={
                        "message": "END Session expired. Dial *123# to start again.",
                        "end_session": True,
                    },
                )

        return MiddlewareResult(proceed=True, context=ctx)


class LoggingMiddleware:
    """Structured logging for all USSD requests."""

    async def before(self, ctx: USSDContext) -> None:
        logger.info(
            "USSD_REQUEST",
            extra={
                "session_id": ctx.session_id,
                "phone": ctx.phone_number[-4:],  # Last 4 digits only
                "provider": ctx.provider,
                "input_length": len(ctx.text),
                "correlation_id": ctx.correlation_id,
            },
        )

    async def after(self, ctx: USSDContext, response: dict, elapsed_ms: int) -> None:
        logger.info(
            "USSD_RESPONSE",
            extra={
                "session_id": ctx.session_id,
                "phone": ctx.phone_number[-4:],
                "provider": ctx.provider,
                "elapsed_ms": elapsed_ms,
                "end_session": response.get("end_session", False),
                "correlation_id": ctx.correlation_id,
            },
        )

        # Alert on slow responses
        if elapsed_ms > 3000:
            logger.warning(
                "USSD_SLOW_RESPONSE",
                extra={
                    "session_id": ctx.session_id,
                    "elapsed_ms": elapsed_ms,
                    "provider": ctx.provider,
                },
            )


class MetricsMiddleware:
    """Tracks USSD performance metrics for Prometheus."""

    _request_count: int = 0
    _error_count: int = 0
    _total_latency_ms: int = 0
    _slow_count: int = 0

    async def record_request(self, provider: str, elapsed_ms: int, error: bool = False) -> None:
        MetricsMiddleware._request_count += 1
        MetricsMiddleware._total_latency_ms += elapsed_ms
        if error:
            MetricsMiddleware._error_count += 1
        if elapsed_ms > 3000:
            MetricsMiddleware._slow_count += 1

    @classmethod
    def get_metrics(cls) -> dict:
        return {
            "total_requests": cls._request_count,
            "total_errors": cls._error_count,
            "total_slow": cls._slow_count,
            "avg_latency_ms": (
                cls._total_latency_ms // cls._request_count
                if cls._request_count > 0
                else 0
            ),
        }


# Module-level instances
validation_middleware = ValidationMiddleware()
retry_middleware = RetryMiddleware()
logging_middleware = LoggingMiddleware()
metrics_middleware = MetricsMiddleware()
