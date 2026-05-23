"""
USSD Replay Tool
================
Record and replay USSD sessions for testing.
"""
from __future__ import annotations

import json
import time
from typing import Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_db

router = APIRouter()


class ReplayStep(BaseModel):
    text: str
    expected_message: str


class ReplaySession(BaseModel):
    phone: str
    provider: str
    steps: List[ReplayStep]


class ReplayResult(BaseModel):
    success: bool
    steps_passed: int
    steps_failed: int
    results: List[dict]


@router.post("/replay", response_model=ReplayResult)
async def replay_session(
    session: ReplaySession,
    db: Any = Depends(get_db),
):
    """Replay a recorded USSD session."""
    from app.ussd.simulator.api import SimulateRequest, simulate_ussd
    import uuid
    
    session_id = f"replay_{uuid.uuid4().hex[:16]}"
    results = []
    passed = 0
    failed = 0
    
    for i, step in enumerate(session.steps):
        try:
            req = SimulateRequest(
                phone=session.phone,
                provider=session.provider,
                text=step.text,
                session_id=session_id,
            )
            response = await simulate_ussd(req, db)
            
            results.append({
                "step": i,
                "input": step.text,
                "response": response.message,
                "expected": step.expected_message,
                "match": step.expected_message in response.message,
            })
            
            if step.expected_message in response.message:
                passed += 1
            else:
                failed += 1
            
            if response.end_session:
                break
                
        except Exception as e:
            results.append({
                "step": i,
                "input": step.text,
                "error": str(e),
                "match": False,
            })
            failed += 1
    
    return ReplayResult(
        success=failed == 0,
        steps_passed=passed,
        steps_failed=failed,
        results=results,
    )
