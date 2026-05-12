"""
Prometheus metrics exporter for ZimAgriTrust backend.
Exposes /metrics in Prometheus text format.
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict
from fastapi import APIRouter, Response
from fastapi import Request

router = APIRouter()

# ── Internal counters (thread-safe) ─────────────────────────────────────────

_lock = threading.Lock()

_request_count: dict[tuple, int]        = defaultdict(int)   # (method, path, status) → count
_request_latency: dict[tuple, list[float]] = defaultdict(list) # (method, path) → [seconds]
_active_requests: dict[str, int]         = defaultdict(int)   # path → count

# Business counters (incremented by services via inc_*)
_counter: dict[str, int | float] = defaultdict(float)

_startup_time = time.time()


# ── Increment helpers (imported by services) ─────────────────────────────────

def inc(metric: str, value: float = 1.0, labels: dict | None = None) -> None:
    key = metric if not labels else f"{metric}{{{','.join(f'{k}={v}' for k,v in labels.items())}}}"
    with _lock:
        _counter[key] += value


def record_request(method: str, path: str, status: int, latency_s: float) -> None:
    with _lock:
        _request_count[(method, path, status)] += 1
        _request_latency[(method, path)].append(latency_s)


def set_active(path: str, delta: int) -> None:
    with _lock:
        _active_requests[path] = max(0, _active_requests[path] + delta)


# ── Prometheus text serialiser ────────────────────────────────────────────────

def _prom_line(name: str, labels: dict, value: float, ts: int | None = None) -> str:
    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    base = f'{name}{{{label_str}}} {value:.6g}'
    return base if ts is None else f"{base} {ts}"


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = max(0, int(len(sorted_v) * pct / 100) - 1)
    return sorted_v[idx]


def _build_prometheus_output() -> str:
    lines: list[str] = []
    now_ms = int(time.time() * 1000)

    # ── Uptime ────────────────────────────────────────────────────────────
    uptime = time.time() - _startup_time
    lines += [
        "# HELP agritrust_uptime_seconds Seconds since backend started",
        "# TYPE agritrust_uptime_seconds gauge",
        f"agritrust_uptime_seconds {uptime:.3f}",
    ]

    # ── HTTP requests ─────────────────────────────────────────────────────
    lines += [
        "# HELP agritrust_http_requests_total Total HTTP requests",
        "# TYPE agritrust_http_requests_total counter",
    ]
    with _lock:
        for (method, path, status), count in _request_count.items():
            lines.append(
                _prom_line(
                    "agritrust_http_requests_total",
                    {"method": method, "path": path, "status": str(status)},
                    count,
                )
            )

    # ── Latency p50 / p95 / p99 ───────────────────────────────────────────
    lines += [
        "# HELP agritrust_http_request_duration_seconds HTTP request latency",
        "# TYPE agritrust_http_request_duration_seconds summary",
    ]
    with _lock:
        for (method, path), latencies in _request_latency.items():
            for q, pct in [(0.5, 50), (0.95, 95), (0.99, 99)]:
                lines.append(
                    _prom_line(
                        "agritrust_http_request_duration_seconds",
                        {"method": method, "path": path, "quantile": str(q)},
                        _percentile(latencies, pct),
                    )
                )
            lines.append(
                _prom_line(
                    "agritrust_http_request_duration_seconds_count",
                    {"method": method, "path": path},
                    len(latencies),
                )
            )
            lines.append(
                _prom_line(
                    "agritrust_http_request_duration_seconds_sum",
                    {"method": method, "path": path},
                    sum(latencies),
                )
            )

    # ── Active requests ───────────────────────────────────────────────────
    lines += [
        "# HELP agritrust_http_requests_active Currently active requests",
        "# TYPE agritrust_http_requests_active gauge",
    ]
    with _lock:
        for path, count in _active_requests.items():
            lines.append(_prom_line("agritrust_http_requests_active", {"path": path}, count))

    # ── Business counters ─────────────────────────────────────────────────
    lines += [
        "# HELP agritrust_business_events_total Business-level event counters",
        "# TYPE agritrust_business_events_total counter",
    ]
    with _lock:
        for metric, value in _counter.items():
            lines.append(f"{metric} {value:.6g}")

    return "\n".join(lines) + "\n"


# ── FastAPI endpoint ──────────────────────────────────────────────────────────

@router.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    """Prometheus scrape endpoint – plain text format."""
    return Response(content=_build_prometheus_output(), media_type="text/plain; version=0.0.4")


# ── Starlette middleware to auto-record request metrics ───────────────────────

class MetricsMiddleware:
    """ASGI middleware that records request count and latency for every request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path   = scope.get("path", "/")
        method = scope.get("method", "UNKNOWN")
        set_active(path, 1)
        start  = time.perf_counter()
        status_code = [200]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code[0] = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency = time.perf_counter() - start
            record_request(method, path, status_code[0], latency)
            set_active(path, -1)
