"""
Structured JSON logging for production.

Wires up a single root-level configuration that:
  - Emits JSON on every log record (level, message, timestamp, logger,
    module, function, line, and any extra= kwargs).
  - Propagates correlation_id from a context-var set by RequestTracingMiddleware.
  - Keeps Uvicorn / SQLAlchemy noise at WARNING unless LOG_LEVEL overrides.
  - Outputs to stdout only; log aggregators (Loki / CloudWatch) consume from there.

Usage:
    from app.core.logging_config import configure_logging
    configure_logging()   # call once at startup, before any loggers are created
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Context variable — set per-request by RequestTracingMiddleware
# ---------------------------------------------------------------------------
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log record to stdout."""

    SKIP = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
    ) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        record.message = record.getMessage()

        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.message,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "correlation_id": correlation_id_var.get("-"),
        }

        # Merge any extra= kwargs that are not standard LogRecord fields
        for key, val in record.__dict__.items():
            if key not in self.SKIP and not key.startswith("_"):
                payload[key] = val

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def configure_logging(log_level: str = "INFO") -> None:
    """
    Install the JSON formatter on the root logger.
    Call exactly once at application startup.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())
    handler.setLevel(level)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quieten noisy third-party loggers
    for noisy in (
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "httpcore",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("app").setLevel(level)
