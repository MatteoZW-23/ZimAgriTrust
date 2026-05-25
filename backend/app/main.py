from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import traceback
import os

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
import app.models # noqa: F401

from app.core.security_middleware import SecurityMiddleware, AuditLoggingMiddleware
from app.core.logging_config import configure_logging
from app.core.tracing_middleware import RequestTracingMiddleware
from app.models.session import UserSession  # noqa: F401 — registers session table
from app.core.health import router as health_router
from app.core.error_tracking import init_sentry
from app.core.metrics import router as metrics_router, MetricsMiddleware
from app.models.system_config import SystemConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(log_level="INFO")
    logger = logging.getLogger("startup")
    logger.info("SYSLOG | Starting ZimAgriTrust backend...")

    init_sentry()
    
    # Initialize USSD flow registry
    try:
        from app.ussd.engine.flow_registry import register_all_flows
        register_all_flows()
        logger.info("SYSLOG | USSD flow registry initialized")
    except Exception as e:
        logger.warning(f"SYSLOG | USSD flow registry initialization failed: {e}")

    testing_mode = os.getenv("APP_ENV", "").lower() in {"test", "testing"} or bool(os.getenv("PYTEST_CURRENT_TEST"))
    try:
        # Schema is managed EXCLUSIVELY by Alembic migrations.
        # create_all() is intentionally removed — it bypasses migration history
        # and causes schema drift in multi-pod deployments.
        # Run `alembic upgrade head` in the Docker entrypoint before starting.

        with SessionLocal() as db:
            logger.info("SYSLOG | Seeding RBAC roles and permissions...")
            from app.services.rbac_service import RBACService
            RBACService.create_default_roles(db)


    except Exception as exc:
        logger.error("BOOT_ERROR | Startup failure: %s", exc, exc_info=True)
        from app.core.error_tracking import capture_exception
        capture_exception(exc, {"context": "startup"})

    # Distributed scheduler: only one pod should run the scheduler.
    # Uses Redis SET NX to elect a leader for the lifetime of this process.
    if not testing_mode:
        from app.services.cache_service import cache_service as _cs
        import asyncio as _asyncio
        _pod_id = os.environ.get("HOSTNAME", str(id(app)))
        _scheduler_lock_key = "scheduler:leader"
        _scheduler_lock_ttl = 120  # seconds; worker must renew before expiry
        _is_scheduler = False
        try:
            _is_scheduler = bool(
                await _cs.set(_scheduler_lock_key, _pod_id, expire=_scheduler_lock_ttl, nx=True)
            )
        except Exception:
            pass

        if _is_scheduler:
            logger.info("SYSLOG | This pod is the scheduler leader (%s).", _pod_id)

            async def _renew_scheduler_lock():
                while True:
                    await _asyncio.sleep(_scheduler_lock_ttl // 2)
                    try:
                        await _cs.set(_scheduler_lock_key, _pod_id, expire=_scheduler_lock_ttl)
                    except Exception:
                        pass
            _asyncio.create_task(_renew_scheduler_lock())
        else:
            logger.info("SYSLOG | Scheduler leader already elected. This pod is a follower.")
    else:
        logger.info("SYSLOG | Testing mode detected; skipping distributed scheduler startup.")

    logger.info("SYSLOG | Platform Live and Ready for Market Deployment.")
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

# 1. CORS Middleware (Must be at the very top to handle preflights before security)
# Restrict to specific frontend origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID", "X-Process-Time", "X-Idempotency-Replayed", "X-CSRF-Token"],
)

# 1.5 Idempotency Middleware (after CORS, before security)
from app.core.idempotency import IdempotencyMiddleware
app.add_middleware(IdempotencyMiddleware)

# 2. Trusted Host Middleware (Skip if wildcard is used)
if settings.ALLOWED_HOSTS.strip() != "*":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# 3. Security & Business Middlewares
app.add_middleware(SecurityMiddleware)

if settings.ADMIN_AUDIT_LOGGING:
    app.add_middleware(AuditLoggingMiddleware)

app.add_middleware(MetricsMiddleware)

# Outermost middleware — sets correlation_id ContextVar before everything else fires
app.add_middleware(RequestTracingMiddleware)


app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(metrics_router)

# --- INDUSTRIAL STRENGTH MIDDLEWARE ---

class EmergencyShutdownMiddleware(BaseHTTPMiddleware):
    """
    Checks SYSTEM_LOCKDOWN flag with a 5-second Redis cache to avoid
    opening a new DB connection on every single mutating request.
    Falls back to allowing the request if Redis is unavailable.
    """
    _CACHE_KEY = "system:lockdown"
    _CACHE_TTL = 5  # seconds

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            path = request.url.path
            if path.startswith("/api/v1/super-admin"):
                return await call_next(request)
            try:
                from app.services.cache_service import cache_service as _cs
                cached = await _cs.get(self._CACHE_KEY)
                if cached is None:
                    with SessionLocal() as db:
                        cfg = db.query(SystemConfig).filter(
                            SystemConfig.key == "SYSTEM_LOCKDOWN"
                        ).first()
                        val = str(cfg.value).lower() if cfg else "false"
                    await _cs.set(self._CACHE_KEY, val, expire=self._CACHE_TTL)
                    cached = val
                if cached == "true":
                    return JSONResponse(
                        status_code=503,
                        content={"detail": "PLATFORM_LOCKDOWN: System under emergency read-only lockdown."},
                    )
            except Exception:
                pass
        return await call_next(request)


class AuditPerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(int(time.time() * 1000)))

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logging.info(
                f"AUDIT | {request.method} {request.url.path} | "
                f"STATUS: {response.status_code} | TIME: {process_time:.4f}s | ID: {request_id}"
            )
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            logging.error(f"SYSTEM FAILURE | ID: {request_id} | ERROR: {str(e)}")
            logging.error(traceback.format_exc())
            raise e


# Register the custom middlewares after they are defined
app.add_middleware(EmergencyShutdownMiddleware)
app.add_middleware(AuditPerformanceMiddleware)


# --- GLOBAL EXCEPTION HANDLING ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected system error occurred. Please contact the Command Center."}
    )


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
