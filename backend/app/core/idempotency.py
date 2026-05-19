"""
Idempotency Middleware for Transaction Endpoints

Race-condition-safe implementation using a two-phase Redis approach:
  Phase 1 — LOCK:   SET NX `idempotency:lock:{key}` with a short TTL (30s).
                    Only ONE request wins this lock. Others see it and wait
                    then retry against the result key.
  Phase 2 — RESULT: On success, write the actual response JSON to
                    `idempotency:result:{key}` with a 24-hour TTL, then
                    delete the lock key.

This eliminates the GET-then-process TOCTOU window where two simultaneous
requests both see an empty cache and both execute.
"""
import asyncio
import uuid
import logging
import json
from typing import Optional, Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

_LOCK_TTL = 30        # seconds — max time a request may hold the processing lock
_RESULT_TTL = 86400   # seconds — 24h result cache
_POLL_INTERVAL = 0.1  # seconds between lock-wait polls
_POLL_TIMEOUT = 25    # seconds max wait for another request to finish processing

_TRANSACTION_PREFIXES = (
    "/api/v1/payments",
    "/api/v1/wallet",
    "/api/v1/deposits",
    "/api/v1/withdrawals",
    "/api/v1/transfers",
    "/api/v1/orders",
)


def _is_transaction_endpoint(path: str) -> bool:
    return any(path.startswith(p) for p in _TRANSACTION_PREFIXES)


def _validate_idempotency_key(key: str) -> bool:
    try:
        uuid.UUID(key)
        return True
    except ValueError:
        pass
    if 16 <= len(key) <= 128 and all(c.isalnum() or c in "-_" for c in key):
        return True
    return False


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Race-condition-safe idempotency middleware.

    Two simultaneous requests with the same Idempotency-Key:
      - Request A wins the SET NX lock → processes normally → writes result → releases lock.
      - Request B fails the SET NX → polls until the result key appears → returns cached result.

    This means the underlying handler executes EXACTLY ONCE per idempotency key,
    regardless of how many concurrent retries arrive.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            if _is_transaction_endpoint(request.url.path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Idempotency-Key header is required for transaction endpoints",
                )
            return await call_next(request)

        if not _validate_idempotency_key(idempotency_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Idempotency-Key format. Use a UUID or 16-128 alphanumeric characters.",
            )

        result_key = f"idempotency:result:{idempotency_key}"
        lock_key = f"idempotency:lock:{idempotency_key}"

        # Fast path: result already cached from a prior completed request.
        cached = await cache_service.get(result_key)
        if cached:
            payload = json.loads(cached)
            return JSONResponse(
                content=payload["body"],
                status_code=payload["status_code"],
                headers={"X-Idempotency-Replayed": "true"},
            )

        # Attempt to acquire the processing lock atomically (SET NX).
        lock_acquired = await cache_service.set(
            lock_key, "1", expire=_LOCK_TTL, nx=True
        )

        if not lock_acquired:
            # Another request is currently processing this key.
            # Poll until the result appears or we time out.
            elapsed = 0.0
            while elapsed < _POLL_TIMEOUT:
                await asyncio.sleep(_POLL_INTERVAL)
                elapsed += _POLL_INTERVAL
                cached = await cache_service.get(result_key)
                if cached:
                    payload = json.loads(cached)
                    return JSONResponse(
                        content=payload["body"],
                        status_code=payload["status_code"],
                        headers={"X-Idempotency-Replayed": "true"},
                    )
            # Timed out — the original request likely crashed. Allow retry by
            # returning 409 so the client can retry with a new key or wait.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A request with this Idempotency-Key is currently being processed. "
                    "Retry after a few seconds."
                ),
            )

        # We hold the lock — process the request.
        try:
            response = await call_next(request)

            # Consume the response body (required to re-serve it).
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            if response.status_code < 400:
                try:
                    body_json = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    body_json = {"raw": body_bytes.decode("utf-8", errors="replace")}

                await cache_service.set(
                    result_key,
                    json.dumps({"body": body_json, "status_code": response.status_code}),
                    expire=_RESULT_TTL,
                )

            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        finally:
            # Always release the processing lock so pollers can terminate.
            await cache_service.delete(lock_key)


def generate_idempotency_key() -> str:
    return str(uuid.uuid4())


async def check_idempotency(idempotency_key: str, operation_type: str) -> Optional[dict]:
    cache_key = f"idempotency:{operation_type}:{idempotency_key}"
    cached = await cache_service.get(cache_key)
    if cached:
        return json.loads(cached)
    return None


async def store_idempotency_result(
    idempotency_key: str,
    operation_type: str,
    result: dict,
    ttl: int = 86400,
) -> None:
    cache_key = f"idempotency:{operation_type}:{idempotency_key}"
    await cache_service.set(cache_key, json.dumps(result), expire=ttl)
