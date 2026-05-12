import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentAssignment, AgentStatus
from app.models.system_audit import SystemAudit
from app.schemas.admin import AgentSummaryResponse, AgentDetailResponse, AgentAssignmentResponse
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/{agent_id}/evaluate-promotion")
def evaluate_agent_promotion(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Re-evaluate an agent's certification level (Trainee → Senior → Master)
    based on current tenure, task volume, accuracy, and rating.
    Idempotent and only ever promotes upward.
    """
    return AgentService.evaluate_promotion(db, agent_id)


@router.get("/{agent_id}/practical-results")
def admin_view_practical_results(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin view of an agent's practical assessment results (4 sub-tests)."""
    from app.models.academy import PracticalAssessment, PracticalTestType
    rows = db.query(PracticalAssessment).filter(PracticalAssessment.agent_id == agent_id).all()
    by_type = {}
    for r in rows:
        key = r.test_type.value if hasattr(r.test_type, "value") else str(r.test_type)
        by_type[key] = {
            "test_type": key,
            "score": r.score,
            "passing_score": r.passing_score,
            "passed": r.passed,
            "attempts": r.attempts,
            "evaluator_notes": r.evaluator_notes,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        }
    all_passed = all(by_type.get(t.value, {}).get("passed") for t in PracticalTestType)
    return {"tests": by_type, "all_passed": all_passed}


@router.get("/{agent_id}/shadowing")
def admin_view_shadowing(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin view of an agent's shadowing logs."""
    from app.models.academy import ShadowingLog, ShadowingStatus
    rows = (
        db.query(ShadowingLog)
        .filter(ShadowingLog.agent_id == agent_id)
        .order_by(ShadowingLog.created_at.desc())
        .all()
    )
    approved = sum(1 for r in rows if r.status == ShadowingStatus.APPROVED)
    return {
        "logs": [
            {
                "id": str(r.id),
                "senior_agent_id": str(r.senior_agent_id),
                "task_type": r.task_type,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "observation_notes": r.observation_notes,
                "agent_actions": r.agent_actions,
                "senior_feedback": r.senior_feedback,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "approved_count": approved,
        "required": 10,
    }


@router.get("/{agent_id}/supervised")
def admin_view_supervised(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Admin view of an agent's supervised independent reviews."""
    from app.models.academy import SupervisedTaskReview
    rows = (
        db.query(SupervisedTaskReview)
        .filter(SupervisedTaskReview.agent_id == agent_id)
        .order_by(SupervisedTaskReview.created_at.desc())
        .all()
    )
    approved = [r for r in rows if r.is_approved]
    avg_acc = (sum(r.accuracy_score or 0 for r in approved) / len(approved)) if approved else 0
    return {
        "reviews": [
            {
                "id": str(r.id),
                "reviewer_agent_id": str(r.reviewer_agent_id) if r.reviewer_agent_id else None,
                "submission": r.submission,
                "review_notes": r.review_notes,
                "accuracy_score": r.accuracy_score,
                "is_approved": r.is_approved,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "approved_count": len(approved),
        "required": 20,
        "average_accuracy": round(avg_acc, 2),
        "min_accuracy_required": 95.0,
    }

@router.get("", response_model=list[AgentSummaryResponse])
def list_agents(
    db: Session = Depends(get_db),
    status: Optional[AgentStatus] = None,
    province: Optional[str] = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 38: View agent list with status and basic stats.
    """
    query = db.query(Agent).options(joinedload(Agent.user))
    if status:
        query = query.filter(Agent.status == status)
    if province:
        query = query.filter(Agent.province == province)
        
    agents = query.all()
    return [
        AgentSummaryResponse(
            id=a.id,
            full_name=a.user.full_name if a.user else "Unknown",
            region=a.province or "Unassigned",
            status=a.status.value,
            rating=a.rating,
            current_load=a.current_load,
            avg_response_time=a.avg_response_time,
            specialization=a.specialization.value
        )
        for a in agents
    ]

@router.get("/stats")
def agent_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Returns granular performance metrics for field agents."""
    agents = db.query(Agent).options(joinedload(Agent.user)).all()
    if not agents:
        basic_agents = db.query(User).filter(User.role == UserRole.AGENT).all()
        return [
            {
                "id": str(u.id), "full_name": u.full_name, "region": u.province or "Central",
                "resolved": 0, "rating": 5.0, "wallet_balance": 0.0, "pending_earnings": 0.0,
                "average_rating": 5.0, "resolution_count": 0,
            } for u in basic_agents
        ]

    return [
        {
            "id": str(a.user_id),
            "full_name": a.user.full_name if a.user else "Anonymous Agent",
            "region": a.user.province if a.user else "Verified Zone",
            "resolved": len([x for x in (a.assignments or []) if x.status == "completed"]),
            "resolution_count": len([x for x in (a.assignments or []) if x.status == "completed"]),
            "rating": round(a.rating, 1) if a.rating else 0.0,
            "average_rating": round(a.rating, 1) if a.rating else 0.0,
            "wallet_balance": round(a.wallet_balance or 0.0, 2),
            "pending_earnings": round(a.pending_earnings or 0.0, 2),
        }
        for a in agents
    ]

@router.get("/{agent_id}", response_model=AgentDetailResponse)
def get_agent_detail(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 41: View agent details and assignment history.
    """
    agent = (
        db.query(Agent)
        .options(joinedload(Agent.user), joinedload(Agent.assignments))
        .filter(Agent.id == agent_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    return AgentDetailResponse(
        id=agent.id,
        full_name=agent.user.full_name if agent.user else "Unknown",
        phone_number=agent.user.phone_number if agent.user else "N/A",
        agent_code=agent.agent_code,
        status=agent.status.value,
        region=f"{agent.province or 'N/A'}, {agent.district or 'N/A'}",
        rating=agent.rating,
        wallet_balance=agent.wallet_balance,
        pending_earnings=agent.pending_earnings,
        assignments=[
            AgentAssignmentResponse(
                id=asgn.id,
                type=asgn.assignment_type,
                target_id=asgn.listing_id or asgn.order_id or asgn.dispute_id or uuid.uuid4(),
                status=asgn.status,
                priority=asgn.priority,
                assigned_at=asgn.assigned_at.isoformat(),
                deadline=asgn.deadline.isoformat() if asgn.deadline else None
            )
            for asgn in agent.assignments
        ]
    )

@router.post("/{agent_id}/status")
def update_agent_status(
    agent_id: uuid.UUID,
    status: AgentStatus,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 57: Suspend agent / Function 58: Terminate agent.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent.status = status
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="AGENT_STATUS_UPDATE",
        target_type="AGENT",
        target_id=agent.id,
        note=reason,
        details={"new_status": status.value}
    )
    db.add(audit)
    db.commit()
    return {"message": f"Agent status updated to {status.value}"}
