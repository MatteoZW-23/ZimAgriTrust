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

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.models # noqa: F401

from app.services.settlement_service import settlement_worker
from app.services.auth_service import build_phone_lookup_candidates, normalize_phone_identifier
from app.models.user import User, UserRole, UserStatus, FarmerProfile, BuyerProfile, AgentProfile
from app.core.security import get_password_hash
from app.services.startup_scraper import run_startup_scrape, start_scheduler
from app.db.schema_patch import apply_schema_patches
from app.core.security_middleware import SecurityMiddleware, AuditLoggingMiddleware
from app.models.session import UserSession  # noqa: F401 — registers session table
from app.core.health import router as health_router
from app.core.error_tracking import init_sentry
from app.core.metrics import router as metrics_router, MetricsMiddleware
from app.models.system_config import SystemConfig
from app.ml.model_loader import model_loader

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("SYSLOG | Initializing Strategic Database Schema...")
    
    # Initialize Sentry error tracking
    init_sentry()
    
    try:
        Base.metadata.create_all(bind=engine)
        print(f"SYSLOG | Tables Confirmed: {list(Base.metadata.tables.keys())}")

        # Patch any columns added to ORM models after the table was first created
        apply_schema_patches(engine)

        with SessionLocal() as db:
            print("SYSLOG | Seeding RBAC roles and permissions...")
            from app.services.rbac_service import RBACService
            RBACService.create_default_roles(db)
            print("SYSLOG | Finalizing Production Environment...")
            settlement_worker.run_settlement_sweep(db)
            print("SYSLOG | Platform Live and Ready for Market Deployment.")

        # Load ONNX and sklearn inference models (non-fatal if weights missing)
        model_loader.load_all()
        print("SYSLOG | ML model loader initialized.")

    except Exception as e:
        print(f"BOOT_ERROR | Managed startup failure: {str(e)}")
        # Capture startup errors in Sentry
        from app.core.error_tracking import capture_exception
        capture_exception(e, {"context": "startup"})

    # ── SCRAPING STARTUP ──────────────────────────────────────────────────
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_startup_scrape)

    start_scheduler()
    print("SYSLOG | Background scraper and scheduler started.")
    # ─────────────────────────────────────────────────────────────────────

    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

# 1. CORS Middleware (Must be at the very top to handle preflights before security)
# Allow credentials with specific origins for admin dashboard, wildcard for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",  # Admin dashboard Vite dev server
        "http://localhost:19000",
        "http://localhost:19001",
        "http://localhost:19002",
        "http://localhost:19006",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:19000",
        "http://127.0.0.1:19002",
        "*",  # Fallback for mobile apps with dynamic IPs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

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


app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(metrics_router)

# --- INDUSTRIAL STRENGTH MIDDLEWARE ---

class EmergencyShutdownMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            path = request.url.path
            if path.startswith("/api/v1/super-admin"):
                return await call_next(request)
            try:
                with SessionLocal() as db:
                    cfg = db.query(SystemConfig).filter(SystemConfig.key == "SYSTEM_LOCKDOWN").first()
                    if cfg and str(cfg.value).lower() == "true":
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
