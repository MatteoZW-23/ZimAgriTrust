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
from app.services.auth_service import get_or_create_master_user, build_phone_lookup_candidates, normalize_phone_identifier
from app.models.user import User, UserRole, UserStatus, FarmerProfile, BuyerProfile, AgentProfile
from app.core.security import get_password_hash

def seed_db(db: SessionLocal):
    # Ensure master test user exists
    get_or_create_master_user(db)
    
    # Define Institutional Default Users
    institutional_users = [
        {"phone": "772222222", "pin": "2222", "role": UserRole.FARMER, "name": "Farmer T. Miller"},
        {"phone": "773333333", "pin": "3333", "role": UserRole.BUYER, "name": "Institutional Buyer (GMB)"},
        {"phone": "778888888", "pin": "8888", "role": UserRole.AGENT, "name": "Field Agent S. Richards"},
        {"phone": "771234567", "pin": "1111", "role": UserRole.ADMIN, "name": "HQ Ops Officer"},
    ]
    
    for u_data in institutional_users:
        canonical = normalize_phone_identifier(u_data["phone"])
        candidates = build_phone_lookup_candidates(canonical)
        
        user = db.query(User).filter(User.phone_number.in_(candidates)).first()
        if not user:
            print(f"SEEDING: Creating Institutional Role [{u_data['role']}] - {u_data['phone']}")
            user = User(
                full_name=u_data["name"],
                phone_number=canonical,
                password_hash=get_password_hash(u_data["pin"]),
                role=u_data["role"],
                status=UserStatus.ACTIVE,
                is_active=True,
                id_verified=True,
                trust_score=80
            )
            db.add(user)
            db.flush() # Get user ID
            
            # Create sub-profiles
            if u_data["role"] == UserRole.FARMER:
                db.add(FarmerProfile(user_id=user.id, farm_name="Green Valley Estate", farm_size_hectares=25.5))
            elif u_data["role"] == UserRole.BUYER:
                db.add(BuyerProfile(user_id=user.id, company_name="Zimbabwe Grain Board", procurement_focus="Maize, Soya"))
from app.services.auth_service import get_or_create_master_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # CRITICAL: Table Creation Sequence
    print("SYSLOG | Initializing Strategic Database Schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print(f"SYSLOG | Tables Confirmed: {list(Base.metadata.tables.keys())}")
        
        with SessionLocal() as db:
            print("SYSLOG | Transitioning to Real-Time Data Ecosystem...")
            # Ensure only the master system user exists for initial setup
            get_or_create_master_user(db)
            
            # The platform is now empty of demo data.
            # Real users and real-time market data will populate the system.
            
            settlement_worker.run_settlement_sweep(db)
            print("SYSLOG | System Live in Real-Time Mode.")

    except Exception as e:
        print(f"BOOT_ERROR | Managed startup failure: {str(e)}")
        
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

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
        # Capture critical system failures
        logging.error(f"SYSTEM FAILURE | ID: {request_id} | ERROR: {str(e)}")
        logging.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Governance Failure",
                "request_id": request_id,
                "error_type": type(e).__name__
            }
        )

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
