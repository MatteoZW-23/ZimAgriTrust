from fastapi import APIRouter

from app.api.v1.endpoints import admin, audit, auth, disputes, listings, market, payments, transactions, ussd, agents, logistics, ai, whatsapp, trades, recruitment, onboarding, requests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(requests.router, prefix="/procurement", tags=["procurement"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(disputes.router, prefix="/disputes", tags=["disputes"])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ussd.router, prefix="/ussd", tags=["ussd"])
api_router.include_router(recruitment.router, prefix="/recruitment", tags=["recruitment"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

