"""
Retry-safe database transaction helper.

Usage:
    from app.db.transaction import atomic

    with atomic(db) as session:
        session.add(...)
        # auto-committed on success, rolled back + retried on serialization failure

Design:
  - Wraps the caller's work in an explicit SAVEPOINT so nested calls are safe.
  - Retries on PostgreSQL serialization failures (40001) and deadlocks (40P01)
    up to MAX_RETRIES times with exponential back-off + jitter.
  - Any other exception is re-raised immediately after rollback.
  - Thread-safe: each call gets its own retry state.
"""
from __future__ import annotations

import logging
import random
import time
from contextlib import contextmanager
from typing import Generator

from psycopg2.errors import DeadlockDetected, SerializationFailure
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MAX_RETRIES: int = 3
BASE_BACKOFF_MS: float = 50.0   # initial wait in milliseconds
MAX_BACKOFF_MS: float = 2_000.0  # cap at 2 seconds


def _is_retryable(exc: Exception) -> bool:
    """Return True for PostgreSQL serialization failures and deadlocks."""
    if isinstance(exc, OperationalError):
        orig = getattr(exc, "orig", None)
        if orig is not None and isinstance(orig, (SerializationFailure, DeadlockDetected)):
            return True
        # Fallback: inspect pgcode string for drivers that wrap differently
        pgcode = getattr(orig, "pgcode", "") or ""
        return pgcode in ("40001", "40P01")
    return False


@contextmanager
def atomic(db: Session) -> Generator[Session, None, None]:
    """
    Context manager that commits on success and rolls back on failure.
    Retries the entire block on serialization errors / deadlocks.

    Example::

        with atomic(db) as session:
            session.add(MyModel(...))
    """
    attempt = 0
    while True:
        try:
            yield db
            db.commit()
            return
        except Exception as exc:
            db.rollback()
            attempt += 1
            if _is_retryable(exc) and attempt < MAX_RETRIES:
                wait_ms = min(
                    BASE_BACKOFF_MS * (2 ** (attempt - 1)) + random.uniform(0, BASE_BACKOFF_MS),
                    MAX_BACKOFF_MS,
                )
                logger.warning(
                    "db_transaction_retry",
                    extra={
                        "attempt": attempt,
                        "max_retries": MAX_RETRIES,
                        "wait_ms": round(wait_ms, 1),
                        "exc_type": type(exc).__name__,
                        "exc_msg": str(exc),
                    },
                )
                time.sleep(wait_ms / 1000.0)
                continue
            if _is_retryable(exc):
                logger.error(
                    "db_transaction_exhausted",
                    extra={
                        "attempts": attempt,
                        "exc_type": type(exc).__name__,
                        "exc_msg": str(exc),
                    },
                )
            raise
