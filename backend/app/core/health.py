"""
Production health checks for PostgreSQL, Redis, Celery queues,
and payment provider configuration.

Endpoints:
  GET /health          — liveness (no deps)
  GET /health/live     — liveness (no deps)
  GET /health/ready    — readiness: DB + Redis must be reachable
  GET /health/detailed — full component breakdown with latency + queue depth
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import redis as redis_sync
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

_START_TS = time.time()

# ---------------------------------------------------------------------------
# Individual component checks
# ---------------------------------------------------------------------------

def _check_postgres(db: Session) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        row = db.execute(text("SELECT version()")).scalar()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "server": (row or "").split(" ")[0:2],
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.error("health_postgres_fail", extra={"error": str(exc)})
        return {"status": "unhealthy", "latency_ms": latency_ms, "error": str(exc)}


def _check_redis() -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = redis_sync.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        info = r.info("server")
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "version": info.get("redis_version"),
            "mode": info.get("redis_mode", "standalone"),
            "uptime_days": info.get("uptime_in_days"),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.error("health_redis_fail", extra={"error": str(exc)})
        return {"status": "unhealthy", "latency_ms": latency_ms, "error": str(exc)}


def _check_queues() -> dict[str, Any]:
    """
    Report Celery queue depths via Redis LIST lengths.
    Queues: default, notifications, payments (see docker-compose celery-worker command).
    """
    queues = ["default", "notifications", "payments"]
    try:
        r = redis_sync.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        depths: dict[str, int] = {}
        for q in queues:
            depths[q] = r.llen(q) or 0
        backlog_warning = any(v > 1000 for v in depths.values())
        return {
            "status": "degraded" if backlog_warning else "healthy",
            "depths": depths,
        }
    except Exception as exc:
        logger.warning("health_queues_unavailable", extra={"error": str(exc)})
        return {"status": "unknown", "error": str(exc)}


def _check_payment_providers() -> dict[str, Any]:
    """
    Verify that payment provider credentials are configured.
    Does NOT make live network calls — this check is intentionally offline.
    """
    results: dict[str, str] = {}

    # Paynow / EcoCash (Zimbabwe)
    paynow_id = getattr(settings, "PAYNOW_INTEGRATION_ID", "")
    paynow_key = getattr(settings, "PAYNOW_INTEGRATION_KEY", "")
    results["paynow"] = (
        "configured" if paynow_id and paynow_key else "missing_credentials"
    )

    # Stripe
    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", "")
    results["stripe"] = "configured" if stripe_key else "missing_credentials"

    # Africa's Talking (mobile money / airtime)
    at_key = getattr(settings, "SMS_API_KEY", "")
    results["africas_talking"] = "configured" if at_key else "missing_credentials"

    any_missing = any(v == "missing_credentials" for v in results.values())
    return {
        "status": "degraded" if any_missing else "healthy",
        "providers": results,
    }


def _check_config() -> dict[str, Any]:
    """Verify critical runtime settings are not placeholder values."""
    insecure = "CHANGE_ME_IN_PRODUCTION"
    issues: list[str] = []
    if insecure in settings.SECRET_KEY:
        issues.append("SECRET_KEY is a placeholder")
    if insecure in getattr(settings, "REFRESH_SECRET_KEY", ""):
        issues.append("REFRESH_SECRET_KEY is a placeholder")
    if not settings.DATABASE_URL:
        issues.append("DATABASE_URL not set")
    if not settings.REDIS_URL:
        issues.append("REDIS_URL not set")
    return {
        "status": "degraded" if issues else "healthy",
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
@router.get("/live")
def liveness():
    """Process is alive — no external dependency checks."""
    return {
        "status": "alive",
        "ts": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _START_TS),
    }


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """
    Readiness: PostgreSQL and Redis must both be reachable.
    Returns 503 when either is unhealthy so k8s / load-balancers stop routing.
    """
    checks = {
        "postgres": _check_postgres(db),
        "redis": _check_redis(),
    }
    healthy = all(c["status"] == "healthy" for c in checks.values())
    body = {
        "status": "ready" if healthy else "not_ready",
        "ts": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    return JSONResponse(status_code=200 if healthy else 503, content=body)


@router.get("/detailed")
def detailed(db: Session = Depends(get_db)):
    """
    Full component breakdown: DB, Redis, queue depths, payment config, runtime config.
    Returns 200 even when degraded — callers inspect each component's status field.
    """
    checks = {
        "postgres":           _check_postgres(db),
        "redis":              _check_redis(),
        "queues":             _check_queues(),
        "payment_providers":  _check_payment_providers(),
        "config":             _check_config(),
    }
    unhealthy = [k for k, v in checks.items() if v["status"] == "unhealthy"]
    degraded  = [k for k, v in checks.items() if v["status"] == "degraded"]

    if unhealthy:
        overall = "unhealthy"
    elif degraded:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "ts": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _START_TS),
        "service": settings.APP_NAME,
        "checks": checks,
    }
