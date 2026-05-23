"""
USSD Metrics
============
Prometheus metrics for USSD infrastructure.
Tracks sessions, errors, latency, provider health.
"""
from __future__ import annotations

import time
import logging
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger("ussd.metrics")

# USSD request metrics
ussd_requests_total = Counter(
    "ussd_requests_total",
    "Total USSD requests processed",
    ["provider", "status"]
)

ussd_request_duration = Histogram(
    "ussd_request_duration_seconds",
    "USSD request processing time",
    ["provider"]
)

ussd_errors_total = Counter(
    "ussd_errors_total",
    "Total USSD errors",
    ["provider", "error_type"]
)

# Session metrics
ussd_active_sessions = Gauge(
    "ussd_active_sessions",
    "Number of active USSD sessions"
)

ussd_sessions_created_total = Counter(
    "ussd_sessions_created_total",
    "Total USSD sessions created",
    ["provider"]
)

ussd_sessions_ended_total = Counter(
    "ussd_sessions_ended_total",
    "Total USSD sessions ended",
    ["provider", "reason"]
)

# Provider health metrics
ussd_provider_health = Gauge(
    "ussd_provider_health",
    "Provider health status (1=healthy, 0=unhealthy)",
    ["provider"]
)

ussd_provider_latency = Histogram(
    "ussd_provider_latency_seconds",
    "Provider callback latency",
    ["provider"]
)

# Retry metrics
ussd_retries_total = Counter(
    "ussd_retries_total",
    "Total USSD retry attempts",
    ["provider"]
)

ussd_duplicates_total = Counter(
    "ussd_duplicates_total",
    "Total duplicate requests detected",
    ["provider"]
)


class USSDMetrics:
    """Central metrics collector for USSD."""

    @staticmethod
    def record_request(provider: str, duration_ms: int, status: str = "success") -> None:
        ussd_requests_total.labels(provider=provider, status=status).inc()
        ussd_request_duration.labels(provider=provider).observe(duration_ms / 1000)

    @staticmethod
    def record_error(provider: str, error_type: str) -> None:
        ussd_errors_total.labels(provider=provider, error_type=error_type).inc()

    @staticmethod
    def record_session_created(provider: str) -> None:
        ussd_sessions_created_total.labels(provider=provider).inc()

    @staticmethod
    def record_session_ended(provider: str, reason: str = "normal") -> None:
        ussd_sessions_ended_total.labels(provider=provider, reason=reason).inc()

    @staticmethod
    def set_active_sessions(count: int) -> None:
        ussd_active_sessions.set(count)

    @staticmethod
    def set_provider_health(provider: str, healthy: bool) -> None:
        ussd_provider_health.labels(provider=provider).set(1 if healthy else 0)

    @staticmethod
    def record_retry(provider: str) -> None:
        ussd_retries_total.labels(provider=provider).inc()

    @staticmethod
    def record_duplicate(provider: str) -> None:
        ussd_duplicates_total.labels(provider=provider).inc()


ussd_metrics = USSDMetrics()
