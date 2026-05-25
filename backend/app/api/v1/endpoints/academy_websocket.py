from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import json
import asyncio

from app.api.deps import get_db, get_current_agent_ws
from app.models.agent import Agent
from app.models.academy import AgentTraining

router = APIRouter()

class ExamTimerManager:
    """Manages exam timer synchronization and auto-submit"""
    
    def __init__(self):
        self.active_sessions = {}  # {agent_id: {"start_time": datetime, "websocket": WebSocket}}
    
    async def register_session(self, agent_id: str, websocket: WebSocket, start_time: datetime):
        """Register an active exam session"""
        self.active_sessions[agent_id] = {
            "start_time": start_time,
            "websocket": websocket
        }
    
    async def unregister_session(self, agent_id: str):
        """Unregister an exam session"""
        if agent_id in self.active_sessions:
            del self.active_sessions[agent_id]
    
    async def start_timer_sync(self, agent_id: str, start_time: datetime, duration_minutes: int = 60):
        """Start timer synchronization for an exam session"""
        expires_at = start_time + timedelta(minutes=duration_minutes)
        
        while agent_id in self.active_sessions:
            now = datetime.now(timezone.utc)
            remaining_seconds = int((expires_at - now).total_seconds())
            
            if remaining_seconds <= 0:
                # Auto-submit on timeout
                await self.auto_submit_exam(agent_id)
                break
            
            # Send timer update every second
            session = self.active_sessions.get(agent_id)
            if session and session["websocket"]:
                try:
                    await session["websocket"].send_json({
                        "type": "timer_update",
                        "remaining_seconds": remaining_seconds,
                        "expires_at": expires_at.isoformat()
                    })
                except:
                    # WebSocket disconnected
                    await self.unregister_session(agent_id)
                    break
            
            await asyncio.sleep(1)
    
    async def auto_submit_exam(self, agent_id: str):
        """Auto-submit exam on timeout"""
        session = self.active_sessions.get(agent_id)
        if session and session["websocket"]:
            try:
                await session["websocket"].send_json({
                    "type": "auto_submit",
                    "reason": "TIMEOUT",
                    "message": "⌛ Session Expired: The 60-minute time limit has been exceeded. Your exam has been auto-submitted."
                })
            except:
                pass
        
        await self.unregister_session(agent_id)

timer_manager = ExamTimerManager()

@router.websocket("/exam/timer/{agent_id}")
async def exam_timer_websocket(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time exam timer synchronization"""
    await websocket.accept()
    
    # Verify agent and active exam session
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        await websocket.close(code=4000, reason="Agent not found")
        return
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent.id).first()
    if not training or not training.last_exam_started_at:
        await websocket.close(code=4001, reason="No active exam session")
        return
    
    # Check if exam has already expired
    elapsed = datetime.now(timezone.utc) - training.last_exam_started_at
    if elapsed > timedelta(minutes=65):
        await websocket.close(code=4002, reason="Exam session expired")
        return
    
    # Register session and start timer sync
    await timer_manager.register_session(agent_id, websocket, training.last_exam_started_at)
    
    # Start timer sync in background
    asyncio.create_task(timer_manager.start_timer_sync(agent_id, training.last_exam_started_at))
    
    try:
        # Handle incoming messages (answer auto-save)
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "answer_save":
                # Auto-save answers (could be persisted to DB)
                question_id = data.get("question_id")
                answer = data.get("answer")
                # Store in temporary cache or DB
                await websocket.send_json({
                    "type": "answer_saved",
                    "question_id": question_id
                })
            
            elif data.get("type") == "heartbeat":
                # Respond to heartbeat to keep connection alive
                await websocket.send_json({"type": "heartbeat_ack"})
    
    except WebSocketDisconnect:
        await timer_manager.unregister_session(agent_id)
    except Exception as e:
        await timer_manager.unregister_session(agent_id)
        await websocket.close(code=4003, reason=str(e))
