from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
            print("SYSLOG | Finalizing Production Environment...")
            settlement_worker.run_settlement_sweep(db)
            print("SYSLOG | Platform Live and Ready for Market Deployment.")

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

# Only apply TrustedHostMiddleware when a specific host list is configured.
# When ALLOWED_HOSTS="*" (default in Docker), skip it — the middleware does NOT
# treat "*" as allow-all; it would redirect every request with a real hostname.
if settings.ALLOWED_HOSTS.strip() != "*":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add audit logging for admin routes
if settings.ADMIN_AUDIT_LOGGING:
    app.add_middleware(AuditLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix="/health", tags=["health"])

# --- INDUSTRIAL STRENGTH MIDDLEWARE ---

@app.middleware("http")
async def audit_and_performance_middleware(request: Request, call_next):
    """
    Middleware for structured logging and performance auditing.
    """
    start_time = time.time()
    
    # Generate request session ID for tracing
    request_id = request.headers.get("X-Request-ID", str(int(time.time() * 1000)))
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log successful request
        logging.info(
            f"AUDIT | {request.method} {request.url.path} | "
            f"STATUS: {response.status_code} | TIME: {process_time:.4f}s | ID: {request_id}"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        # Capture and log critical system failures, then re-raise so CORSMiddleware catches it
        logging.error(f"SYSTEM FAILURE | ID: {request_id} | ERROR: {str(e)}")
        logging.error(traceback.format_exc())
        raise e

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
