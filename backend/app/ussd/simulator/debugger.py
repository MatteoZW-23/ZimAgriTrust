"""
USSD Session Debugger
=====================
Inspect and debug USSD session state in real-time.
"""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import get_db
from app.ussd.engine.redis_session_store import session_store

router = APIRouter()


@router.get("/debug/session/{session_id}")
async def debug_session(session_id: str):
    """Get full session state for debugging."""
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session": session.to_dict(),
        "is_expired": session.is_expired,
        "is_authenticated": session.is_authenticated,
    }


@router.get("/debug/phone/{phone}")
async def debug_by_phone(phone: str):
    """Find session by phone number."""
    session = await session_store.get_session_by_phone(phone)
    if not session:
        raise HTTPException(status_code=404, detail="No active session for this phone")
    return session.to_dict()


@router.post("/debug/session/{session_id}/extend")
async def extend_session_debug(session_id: str, seconds: int = 60):
    """Extend session TTL for debugging."""
    success = await session_store.extend_session(session_id, seconds)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "extended", "seconds": seconds}


@router.get("/debug/stats")
async def debug_stats():
    """Get Redis and session statistics."""
    active = await session_store.get_active_session_count()
    cleaned = await session_store.cleanup_expired()
    return {"active_sessions": active, "cleaned_expired": cleaned}
