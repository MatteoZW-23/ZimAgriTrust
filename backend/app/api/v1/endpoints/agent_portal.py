from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.agent import Agent, AgentAssignment
from app.models.user import User, UserRole
from app.services.agent_earnings_service import AgentEarningsService
from app.services.fee_engine import FeeEngine, FeeConfig, AgentTier

router = APIRouter()


class RejectTaskPayload(BaseModel):
    reason: str


class VerificationReportPayload(BaseModel):
    farmer_identity_ok: bool = True
    crop_exists: bool = True
    estimated_quantity_kg: float | None = None
    grade: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    photo_urls: list[str] = Field(default_factory=list)
    notes: str = ""
    recommendation: str = "approve"


def _current_agent(db: Session, user: User) -> Agent:
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    if not agent:
        raise HTTPException(status_code=403, detail="Agent profile is not active for this account.")
    return agent


def _serialize_assignment(row: AgentAssignment) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "assignment_type": row.assignment_type,
        "listing_id": str(row.listing_id) if row.listing_id else None,
        "order_id": str(row.order_id) if row.order_id else None,
        "dispute_id": str(row.dispute_id) if row.dispute_id else None,
        "status": row.status,
        "priority": row.priority,
        "assigned_at": row.assigned_at,
        "accepted_at": row.accepted_at,
        "completed_at": row.completed_at,
        "deadline": row.deadline,
        "notes": row.agent_notes,
        "resolution": row.resolution,
        "bounty_amount": row.bounty_amount,
        "bonus_amount": row.bonus_amount,
        "is_paid": row.is_paid,
    }


@router.get("/tasks")
def list_agent_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> list[dict[str, Any]]:
    agent = _current_agent(db, current_user)
    rows = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.agent_id == agent.id)
        .order_by(AgentAssignment.assigned_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_assignment(row) for row in rows]


@router.post("/tasks/{task_id}/accept")
def accept_agent_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> dict[str, Any]:
    agent = _current_agent(db, current_user)
    task = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.id == task_id, AgentAssignment.agent_id == agent.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    task.status = "accepted"
    task.accepted_at = datetime.now(timezone.utc)
    agent.current_load += 1
    db.commit()
    db.refresh(task)
    return _serialize_assignment(task)


@router.post("/tasks/{task_id}/reject")
def reject_agent_task(
    task_id: uuid.UUID,
    payload: RejectTaskPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> dict[str, Any]:
    agent = _current_agent(db, current_user)
    task = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.id == task_id, AgentAssignment.agent_id == agent.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    task.status = "rejected"
    task.agent_notes = payload.reason
    db.commit()
    db.refresh(task)
    return _serialize_assignment(task)


@router.post("/tasks/{task_id}/report")
def submit_agent_report(
    task_id: uuid.UUID,
    payload: VerificationReportPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> dict[str, Any]:
    agent = _current_agent(db, current_user)
    task = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.id == task_id, AgentAssignment.agent_id == agent.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.agent_notes = payload.notes
    task.resolution = payload.model_dump_json()
    agent.current_load = max(0, agent.current_load - 1)
    db.commit()
    db.refresh(task)
    return {"message": "Verification report submitted.", "task": _serialize_assignment(task)}


@router.get("/earnings")
def get_agent_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> dict[str, Any]:
    """Get agent earnings breakdown including commission details."""
    agent = _current_agent(db, current_user)
    
    # Get agent tier
    agent_tier = FeeEngine.determine_agent_tier(agent.rating)
    tier_multiplier = FeeConfig.AGENT_TIER_MULTIPLIERS.get(agent_tier, 1.0)
    
    # Get completed assignments with earnings
    completed_assignments = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.agent_id == agent.id, AgentAssignment.status == "completed")
        .order_by(AgentAssignment.completed_at.desc())
        .limit(50)
        .all()
    )
    
    # Group by service type
    earnings_by_service = {
        "verification": {"count": 0, "total": 0.0, "assignments": []},
        "dispute_resolution": {"count": 0, "total": 0.0, "assignments": []},
        "order_fulfillment": {"count": 0, "total": 0.0, "assignments": []},
        "field_support": {"count": 0, "total": 0.0, "assignments": []},
        "onboarding": {"count": 0, "total": 0.0, "assignments": []},
    }
    
    for assignment in completed_assignments:
        service_type = assignment.assignment_type
        if service_type == "listing":
            service_type = "verification"
        elif service_type == "dispute":
            service_type = "dispute_resolution"
        
        if service_type in earnings_by_service:
            earnings_by_service[service_type]["count"] += 1
            earnings_by_service[service_type]["total"] += assignment.bounty_amount or 0.0
            earnings_by_service[service_type]["assignments"].append({
                "id": str(assignment.id),
                "amount": assignment.bounty_amount or 0.0,
                "bonus": assignment.bonus_amount or 0.0,
                "completed_at": assignment.completed_at,
            })
    
    # Calculate totals
    total_earnings = sum(s["total"] for s in earnings_by_service.values())
    total_assignments = sum(s["count"] for s in earnings_by_service.values())
    
    return {
        "agent_id": str(agent.id),
        "agent_code": agent.agent_code,
        "rating": agent.rating,
        "tier": agent_tier.value,
        "tier_multiplier": tier_multiplier,
        "wallet_balance": agent.wallet_balance,
        "pending_earnings": agent.pending_earnings or 0.0,
        "total_earnings": total_earnings,
        "total_assignments": total_assignments,
        "earnings_by_service": earnings_by_service,
        "commission_rates": {
            "verification": FeeConfig.AGENT_VERIFICATION_COMMISSION_PERCENT,
            "dispute_resolution": FeeConfig.AGENT_DISPUTE_RESOLUTION_COMMISSION_PERCENT,
            "order_fulfillment": FeeConfig.AGENT_ORDER_FULFILLMENT_COMMISSION_PERCENT,
            "field_support": FeeConfig.AGENT_FIELD_SUPPORT_COMMISSION_PERCENT,
            "onboarding": FeeConfig.AGENT_ONBOARDING_COMMISSION_PERCENT,
        },
        "pending_earnings": float(agent.pending_earnings or 0),
        "total": float((agent.wallet_balance or 0) + (agent.pending_earnings or 0)),
    }


@router.get("/performance")
def agent_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.AGENT)),
) -> dict[str, Any]:
    agent = _current_agent(db, current_user)
    total_tasks = db.query(AgentAssignment).filter(AgentAssignment.agent_id == agent.id).count()
    completed = (
        db.query(AgentAssignment)
        .filter(AgentAssignment.agent_id == agent.id, AgentAssignment.status == "completed")
        .count()
    )
    return {
        "agent_code": agent.agent_code,
        "rating": agent.rating,
        "total_tasks": total_tasks,
        "completed_tasks": completed,
        "current_load": agent.current_load,
        "status": agent.status,
        "avg_response_time_hours": agent.avg_response_time,
    }
