"""
Agent Shadowing & Supervised Independent Period — `/api/v1/agents/{shadowing,supervised}/*`

After all 4 practical tests pass:
  • Shadowing: complete 10 tasks while observing a senior agent (senior signs off)
  • Supervised: complete 20 independent tasks reviewed by a senior (95% accuracy)

After both, the admin can flip the agent to ACTIVE.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.agent import Agent
from app.models.academy import (
    AgentTraining,
    ShadowingLog,
    ShadowingStatus,
    SupervisedTaskReview,
)
from app.models.user import User, UserRole

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ShadowingComplete(BaseModel):
    senior_feedback: Optional[str] = Field(None, max_length=2000)
    status: ShadowingStatus = ShadowingStatus.APPROVED


class ShadowingCreate(BaseModel):
    senior_agent_id: uuid.UUID
    assignment_id: Optional[uuid.UUID] = None
    task_type: str
    observation_notes: Optional[str] = None
    agent_actions: Optional[str] = None


class SupervisedSubmission(BaseModel):
    assignment_id: Optional[uuid.UUID] = None
    submission: dict


class SupervisedReview(BaseModel):
    review_notes: Optional[str] = None
    accuracy_score: float = Field(..., ge=0, le=100)
    is_approved: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agent_for(user: User, db: Session) -> Agent:
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="No agent profile")
    return agent


def _serialize_shadowing(row: ShadowingLog) -> dict:
    return {
        "id": str(row.id),
        "agent_id": str(row.agent_id),
        "senior_agent_id": str(row.senior_agent_id),
        "assignment_id": str(row.assignment_id) if row.assignment_id else None,
        "task_type": row.task_type,
        "observation_notes": row.observation_notes,
        "agent_actions": row.agent_actions,
        "senior_feedback": row.senior_feedback,
        "status": row.status.value if hasattr(row.status, "value") else row.status,
        "approved_at": row.approved_at.isoformat() if row.approved_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_supervised(row: SupervisedTaskReview) -> dict:
    return {
        "id": str(row.id),
        "agent_id": str(row.agent_id),
        "reviewer_agent_id": str(row.reviewer_agent_id) if row.reviewer_agent_id else None,
        "assignment_id": str(row.assignment_id) if row.assignment_id else None,
        "submission": row.submission,
        "review_notes": row.review_notes,
        "accuracy_score": row.accuracy_score,
        "is_approved": row.is_approved,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# ---------------------------------------------------------------------------
# Shadowing — junior view
# ---------------------------------------------------------------------------

@router.get("/shadowing/tasks")
def list_my_shadowing_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    agent = _agent_for(user, db)
    rows = (
        db.query(ShadowingLog)
        .filter(ShadowingLog.agent_id == agent.id)
        .order_by(ShadowingLog.created_at.desc())
        .all()
    )
    approved_count = sum(1 for r in rows if r.status == ShadowingStatus.APPROVED)
    return {
        "logs": [_serialize_shadowing(r) for r in rows],
        "approved_count": approved_count,
        "required": 10,
        "remaining": max(0, 10 - approved_count),
    }


@router.post("/shadowing")
def create_shadowing_log(
    payload: ShadowingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    agent = _agent_for(user, db)
    log = ShadowingLog(
        agent_id=agent.id,
        senior_agent_id=payload.senior_agent_id,
        assignment_id=payload.assignment_id,
        task_type=payload.task_type,
        observation_notes=payload.observation_notes,
        agent_actions=payload.agent_actions,
        status=ShadowingStatus.PENDING,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _serialize_shadowing(log)


@router.post("/shadowing/{log_id}/complete")
def complete_shadowing(
    log_id: uuid.UUID,
    payload: ShadowingComplete,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    """Senior agent signs off on a shadowing log."""
    senior_agent = _agent_for(user, db)
    log = db.query(ShadowingLog).filter(ShadowingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Shadowing log not found")
    if log.senior_agent_id != senior_agent.id:
        raise HTTPException(status_code=403, detail="Only the assigned senior agent can sign this off")

    log.status = payload.status
    log.senior_feedback = payload.senior_feedback
    if payload.status == ShadowingStatus.APPROVED:
        log.approved_at = datetime.now(timezone.utc)
        # Bump junior's training counter
        training = db.query(AgentTraining).filter(AgentTraining.agent_id == log.agent_id).first()
        if training:
            training.shadowing_tasks_completed = (training.shadowing_tasks_completed or 0) + 1
    db.commit()
    db.refresh(log)
    return _serialize_shadowing(log)


# ---------------------------------------------------------------------------
# Supervised independent — junior submits, senior reviews
# ---------------------------------------------------------------------------

@router.get("/supervised/tasks")
def list_my_supervised_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    agent = _agent_for(user, db)
    rows = (
        db.query(SupervisedTaskReview)
        .filter(SupervisedTaskReview.agent_id == agent.id)
        .order_by(SupervisedTaskReview.created_at.desc())
        .all()
    )
    approved = [r for r in rows if r.is_approved]
    avg_accuracy = (
        sum(r.accuracy_score or 0 for r in approved) / len(approved) if approved else 0
    )
    return {
        "reviews": [_serialize_supervised(r) for r in rows],
        "approved_count": len(approved),
        "required": 20,
        "remaining": max(0, 20 - len(approved)),
        "average_accuracy": round(avg_accuracy, 2),
        "min_accuracy_required": 95.0,
    }


@router.post("/supervised/{task_id}/submit")
def submit_supervised_task(
    task_id: uuid.UUID,
    payload: SupervisedSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    """Junior agent submits their report for senior review."""
    agent = _agent_for(user, db)
    review = SupervisedTaskReview(
        agent_id=agent.id,
        assignment_id=payload.assignment_id or task_id,
        submission=payload.submission,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _serialize_supervised(review)


@router.post("/supervised/{review_id}/review")
def review_supervised_task(
    review_id: uuid.UUID,
    payload: SupervisedReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    """Senior agent reviews a junior's supervised submission."""
    reviewer = _agent_for(user, db)
    review = db.query(SupervisedTaskReview).filter(SupervisedTaskReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.reviewer_agent_id = reviewer.id
    review.review_notes = payload.review_notes
    review.accuracy_score = payload.accuracy_score
    review.is_approved = payload.is_approved
    review.reviewed_at = datetime.now(timezone.utc)

    if payload.is_approved:
        training = db.query(AgentTraining).filter(AgentTraining.agent_id == review.agent_id).first()
        if training:
            training.supervised_tasks_completed = (training.supervised_tasks_completed or 0) + 1

    db.commit()
    db.refresh(review)
    return _serialize_supervised(review)
