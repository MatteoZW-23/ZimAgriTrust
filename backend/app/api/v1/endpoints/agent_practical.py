"""
Agent Practical Assessment — `/api/v1/agents/practical/*`

Four sub-tests taken AFTER the final exam, BEFORE shadowing:
  • grading-test       (90% required)
  • app-test           (100% required)
  • photo-test         (90% required)
  • dispute-roleplay   (80% required)

Each endpoint upserts a PracticalAssessment row keyed by (agent_id, test_type).
The agent must pass all four to advance to shadowing.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps import require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.academy import (
    AgentTraining,
    PracticalAssessment,
    PracticalTestType,
)

router = APIRouter()


# ── passing thresholds (per spec Part 2.1 Step 6) ──────────────────────────
PASSING_SCORES = {
    PracticalTestType.GRADING: 90.0,
    PracticalTestType.APP_NAVIGATION: 100.0,
    PracticalTestType.PHOTO_EVIDENCE: 90.0,
    PracticalTestType.DISPUTE_ROLEPLAY: 80.0,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PracticalSubmission(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Score as a percentage (0-100)")
    answers: Optional[dict] = None
    evaluator_notes: Optional[str] = Field(None, max_length=2000)


class PracticalResult(BaseModel):
    test_type: str
    score: float
    passing_score: float
    passed: bool
    attempts: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_agent_for_user(db: Session, user: User) -> Agent:
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="No agent profile for current user")
    return agent


def _ensure_final_exam_passed(db: Session, agent_id) -> None:
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent_id).first()
    if not training or not training.final_exam_score or training.final_exam_score < 80:
        raise HTTPException(
            status_code=403,
            detail="Final exam (80% pass) must be completed before practical assessment.",
        )


def _upsert_practical(
    db: Session,
    agent_id,
    test_type: PracticalTestType,
    submission: PracticalSubmission,
) -> PracticalAssessment:
    pass_score = PASSING_SCORES[test_type]
    row = (
        db.query(PracticalAssessment)
        .filter(
            PracticalAssessment.agent_id == agent_id,
            PracticalAssessment.test_type == test_type,
        )
        .first()
    )
    if row:
        row.score = submission.score
        row.passing_score = pass_score
        row.passed = submission.score >= pass_score
        row.answers = submission.answers
        row.evaluator_notes = submission.evaluator_notes
        row.attempts = (row.attempts or 0) + 1
    else:
        row = PracticalAssessment(
            agent_id=agent_id,
            test_type=test_type,
            score=submission.score,
            passing_score=pass_score,
            passed=submission.score >= pass_score,
            answers=submission.answers,
            evaluator_notes=submission.evaluator_notes,
            attempts=1,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _result(row: PracticalAssessment) -> PracticalResult:
    return PracticalResult(
        test_type=row.test_type.value if hasattr(row.test_type, "value") else str(row.test_type),
        score=row.score,
        passing_score=row.passing_score,
        passed=row.passed,
        attempts=row.attempts,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# REMOVED: /grading-test, /app-test, /photo-test endpoints - Development-only, not for production
# Agent practical tests should be managed through the Academy system


@router.post("/dispute-roleplay", response_model=PracticalResult)
def submit_dispute_roleplay(
    payload: PracticalSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    agent = _get_agent_for_user(db, user)
    _ensure_final_exam_passed(db, agent.id)
    return _result(_upsert_practical(db, agent.id, PracticalTestType.DISPUTE_ROLEPLAY, payload))


@router.get("/results")
def get_practical_results(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AGENT)),
):
    agent = _get_agent_for_user(db, user)
    rows = (
        db.query(PracticalAssessment)
        .filter(PracticalAssessment.agent_id == agent.id)
        .all()
    )
    by_type = {row.test_type.value if hasattr(row.test_type, "value") else str(row.test_type): _result(row).model_dump() for row in rows}
    all_passed = all(by_type.get(t.value, {}).get("passed") for t in PracticalTestType)
    return {
        "tests": by_type,
        "all_passed": all_passed,
        "next_step": "shadowing" if all_passed else "retake_failed_tests",
    }
