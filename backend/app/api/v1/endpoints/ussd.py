from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db
from app.ussd.webhook_handler import handle_ussd_webhook

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/session")
async def handle_ussd(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """USSD session endpoint using state machine architecture."""
    try:
        response = await handle_ussd_webhook(request, background_tasks, db, provider=None)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"USSD session error: {str(e)}")
        raise HTTPException(status_code=500, detail="USSD service error")


@router.post("/webhook/{provider}")
async def ussd_webhook_provider(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """USSD webhook for specific provider (econet, netone, telecel)."""
    try:
        response = await handle_ussd_webhook(request, background_tasks, db, provider)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"USSD webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="USSD service error")


@router.get("/health")
async def ussd_health():
    """USSD service health check."""
    from app.ussd.engine.redis_session_store import session_store
    from app.ussd.engine.state_machine import state_machine
    from app.ussd.engine.retry_handler import retry_handler
    
    active_sessions = await session_store.get_active_session_count()
    circuit_status = await retry_handler.get_circuit_breaker_status()
    
    return {
        "status": "healthy",
        "active_sessions": active_sessions,
        "registered_screens": len(state_machine.get_registered_screens()),
        "circuit_breaker": circuit_status,
    }
