"""
USSD Tracing
============
Distributed tracing for USSD request flows.
Integrates with Tempo/Jaeger for end-to-end visibility.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

logger = logging.getLogger("ussd.tracing")


class USSDTracer:
    """Simple tracer for USSD request flows."""

    @staticmethod
    def start_trace(session_id: str, phone: str, provider: str) -> str:
        """Start a new trace and return trace ID."""
        trace_id = uuid.uuid4().hex
        logger.info(
            "TRACE_START",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "phone": phone[-4:],
                "provider": provider,
            },
        )
        return trace_id

    @staticmethod
    def span(trace_id: str, operation: str, details: dict = None) -> None:
        """Record a span within a trace."""
        logger.info(
            f"TRACE_SPAN_{operation.upper()}",
            extra={
                "trace_id": trace_id,
                "operation": operation,
                "details": details or {},
            },
        )

    @staticmethod
    def end_trace(trace_id: str, status: str = "success") -> None:
        """End a trace."""
        logger.info(
            "TRACE_END",
            extra={"trace_id": trace_id, "status": status},
        )


ussd_tracer = USSDTracer()
