"""Monitoring and observability for WhatsApp service."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates metrics for the WhatsApp service."""

    def __init__(self):
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        self._start_time = time.time()

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self._counters[name] += value
        logger.debug(f"Counter {name} incremented by {value}, total: {self._counters[name]}")

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric."""
        self._gauges[name] = value
        logger.debug(f"Gauge {name} set to {value}")

    def record_histogram(self, name: str, value: float) -> None:
        """Record a value in a histogram."""
        self._histograms[name].append(value)
        # Keep only last 1000 values to prevent memory issues
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]
        logger.debug(f"Histogram {name} recorded value {value}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        uptime = time.time() - self._start_time

        # Calculate histogram statistics
        histogram_stats = {}
        for name, values in self._histograms.items():
            if values:
                histogram_stats[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                }

        return {
            "uptime_seconds": uptime,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": histogram_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def percentile(values: list, p: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_time = time.time()
        logger.info("Metrics reset")


class HealthChecker:
    """Health check endpoints for the WhatsApp service."""

    def __init__(self, metrics: MetricsCollector):
        self._metrics = metrics

    async def check_health(self) -> Dict[str, Any]:
        """Basic health check."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_readiness(self) -> Dict[str, Any]:
        """Readiness check - is the service ready to handle traffic?"""
        metrics = self._metrics.get_metrics()
        uptime = metrics.get("uptime_seconds", 0)

        # Service is ready if it's been up for at least 10 seconds
        ready = uptime >= 10

        return {
            "ready": ready,
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_liveness(self) -> Dict[str, Any]:
        """Liveness check - is the service still running?"""
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for monitoring."""
        return self._metrics.get_metrics()


# Global metrics instance
_metrics_collector: MetricsCollector = MetricsCollector()
_health_checker: HealthChecker = HealthChecker(_metrics_collector)


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics_collector


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    return _health_checker
