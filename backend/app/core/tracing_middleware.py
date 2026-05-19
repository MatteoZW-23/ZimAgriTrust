"""
Request tracing middleware.

Per-request responsibilities:
  1. Read or generate a UUID4 correlation ID from X-Request-ID header.
  2. Store it in a ContextVar so every log record emitted during the request
     automatically includes it (via _JSONFormatter in logging_config.py).
  3. Emit structured access logs at request start and end with:
       method, path, status_code, duration_ms, client_ip, user_agent
  4. Emit structured 4xx / 5xx log records at appropriate severity levels.
  5. Propagate the correlation ID back to the caller via X-Request-ID
     and X-Correlation-ID response headers.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import correlation_id_var

logger = logging.getLogger("app.access")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ── 1. Correlation ID ──────────────────────────────────────────────
        cid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = correlation_id_var.set(cid)

        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")[:200]
        start = time.perf_counter()

        # ── 2. Request start log ──────────────────────────────────────────
        logger.debug(
            "request_started",
            extra={
                "http_method": request.method,
                "http_path": request.url.path,
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        # ── 3. Process request ────────────────────────────────────────────
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request_unhandled_exception",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "client_ip": client_ip,
                    "duration_ms": duration_ms,
                    "exc_type": type(exc).__name__,
                    "exc_msg": str(exc),
                },
                exc_info=True,
            )
            correlation_id_var.reset(token)
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        status = response.status_code

        # ── 4. Structured 4xx / 5xx logging ──────────────────────────────
        log_extra = {
            "http_method": request.method,
            "http_path": request.url.path,
            "http_status": status,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
            "user_agent": user_agent,
        }
        if status >= 500:
            logger.error("request_server_error", extra=log_extra)
        elif status >= 400:
            logger.warning("request_client_error", extra=log_extra)
        else:
            logger.info("request_completed", extra=log_extra)

        # ── 5. Propagate correlation ID ───────────────────────────────────
        response.headers["X-Request-ID"] = cid
        response.headers["X-Correlation-ID"] = cid

        correlation_id_var.reset(token)
        return response


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"
