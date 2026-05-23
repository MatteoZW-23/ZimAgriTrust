"""
USSD Alerts
===========
Alert conditions for USSD infrastructure.
Triggers on high error rates, slow responses, provider issues.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("ussd.alerts")


class USSDAlertManager:
    """Manages USSD alert conditions."""

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.05  # 5% error rate
    LATENCY_THRESHOLD_MS = 3000  # 3 seconds
    RETRY_STORM_THRESHOLD = 100  # retries per minute
    CIRCUIT_BREAKER_THRESHOLD = 50

    def __init__(self):
        self._error_count = 0
        self._total_requests = 0
        self._slow_count = 0
        self._alerted = False

    def record_request(self, success: bool, latency_ms: int) -> None:
        """Record a request outcome."""
        self._total_requests += 1
        if not success:
            self._error_count += 1
        if latency_ms > self.LATENCY_THRESHOLD_MS:
            self._slow_count += 1

    def check_alerts(self) -> Optional[str]:
        """Check if any alert conditions are met."""
        if self._total_requests == 0:
            return None

        error_rate = self._error_count / self._total_requests
        slow_rate = self._slow_count / self._total_requests

        if error_rate > self.ERROR_RATE_THRESHOLD:
            alert = f"High error rate: {error_rate:.1%}"
            logger.warning("USSD_ALERT", extra={"alert": alert, "error_rate": error_rate})
            return alert

        if slow_rate > 0.1:  # 10% slow
            alert = f"High slow rate: {slow_rate:.1%}"
            logger.warning("USSD_ALERT", extra={"alert": alert, "slow_rate": slow_rate})
            return alert

        return None

    def reset(self) -> None:
        """Reset counters."""
        self._error_count = 0
        self._total_requests = 0
        self._slow_count = 0


ussd_alerts = USSDAlertManager()
