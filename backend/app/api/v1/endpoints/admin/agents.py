import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentAssignment, AgentStatus
from app.models.system_audit import SystemAudit
from app.schemas.admin import AgentSummaryResponse, AgentDetailResponse, AgentAssignmentResponse

router = APIRouter()

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

@router.get("/stats")
def agent_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Returns granular performance metrics for field agents (Legacy compat)."""
    agents = db.query(Agent).options(joinedload(Agent.user)).all()
    if not agents:
        basic_agents = db.query(User).filter(User.role == UserRole.AGENT).all()
        return [
            {
                "id": str(u.id), "full_name": u.full_name, "region": u.province or "Central",
                "resolved": 0, "rating": 5.0
            } for u in basic_agents
        ]

    return [
        {
            "id": str(a.user_id),
            "full_name": a.user.full_name if a.user else "Anonymous Agent",
            "region": a.user.province if a.user else "Verified Zone",
            "resolved": len(a.assignments) if a.assignments else 0,
            "rating": a.rating
        }
        for a in agents
    ]

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
