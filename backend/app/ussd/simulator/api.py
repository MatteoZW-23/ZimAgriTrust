"""
USSD Simulator API
==================
FastAPI endpoints for simulating USSD sessions from Zimbabwe telcos.
Supports Econet, NetOne, Telecel with realistic payload formats.
"""
from __future__ import annotations

import uuid
import time
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_db
from app.ussd.webhook_handler import handle_ussd_webhook
from app.ussd.engine.redis_session_store import session_store

router = APIRouter()


class SimulateRequest(BaseModel):
    phone: str
    provider: str = "econet"
    text: str = ""
    session_id: Optional[str] = None


class SimulateResponse(BaseModel):
    message: str
    session_id: str
    end_session: bool
    provider: str
    elapsed_ms: int


@router.post("/simulate", response_model=SimulateResponse)
async def simulate_ussd(
    request: SimulateRequest,
    db: Any = Depends(get_db),
):
    """Simulate a USSD request from a Zimbabwe telco."""
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = request.session_id or f"sim_{uuid.uuid4().hex[:16]}"
    
    # Build provider-specific payload
    if request.provider == "econet":
        payload = {
            "sessionId": session_id,
            "phoneNumber": request.phone,
            "text": request.text,
            "serviceCode": "*123#",
            "networkCode": "64501",
        }
    elif request.provider == "netone":
        payload = {
            "session_id": session_id,
            "msisdn": request.phone,
            "ussd_string": request.text,
            "short_code": "*123#",
            "msg_type": "initiation" if not request.text else "response",
        }
    elif request.provider == "telecel":
        payload = {
            "sid": session_id,
            "phone": request.phone,
            "input": request.text,
            "code": "*123#",
            "type": "begin" if not request.text else "continue",
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
    
    # Create mock request
    from fastapi import Request
    class MockRequest:
        def __init__(self, payload):
            self._payload = payload
        async def json(self):
            return self._payload
        @property
        def headers(self):
            return {}
    
    mock_req = MockRequest(payload)
    
    # Process through USSD infrastructure
    from fastapi import BackgroundTasks
    bg_tasks = BackgroundTasks()
    
    try:
        response = await handle_ussd_webhook(mock_req, bg_tasks, db, request.provider)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Extract message from provider response
        message = response.get("response", response.get("ussd_response", response.get("msg", "END Error")))
        end_session = response.get("endSession", response.get("session_end", response.get("end", False)))
        
        return SimulateResponse(
            message=message,
            session_id=session_id,
            end_session=end_session,
            provider=request.provider,
            elapsed_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/session/{session_id}")
async def get_simulator_session(session_id: str):
    """Get current session state for debugging."""
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.delete("/session/{session_id}")
async def destroy_simulator_session(session_id: str):
    """Destroy a simulator session."""
    await session_store.destroy_session(session_id)
    return {"status": "destroyed", "session_id": session_id}


@router.get("/stats")
async def get_simulator_stats():
    """Get simulator statistics."""
    active_sessions = await session_store.get_active_session_count()
    return {"active_sessions": active_sessions}
