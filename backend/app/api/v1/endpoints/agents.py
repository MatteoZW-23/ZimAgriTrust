import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.listing import Listing
from app.models.dispute import Dispute
from app.models.agent import Agent, AgentAssignment
from app.schemas.agent import AgentResponse, AgentAssignmentResponse, VerificationReportCreate, DeliveryReportCreate
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/assignments/me", response_model=List[AgentAssignmentResponse])
def get_my_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assignments for the logged-in agent"""
    if current_user.role != UserRole.AGENT and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent profile not found"
        )
    
    return db.query(AgentAssignment).filter(
        AgentAssignment.agent_id == agent.id,
        AgentAssignment.status.in_(["assigned", "accepted"])
    ).all()

@router.post("/assignments/{assignment_id}/accept")
def accept_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agent accepts an assignment"""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")

    return AgentService.accept_task(db, assignment_id, current_user)

@router.post("/verify")
def submit_verification(
    payload: VerificationReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a physical listing verification report"""
    return AgentService.submit_verification_report(db, payload, current_user)

@router.post("/delivery")
def submit_delivery(
    payload: DeliveryReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a delivery handover confirmation"""
    return AgentService.submit_delivery_confirmation(db, payload, current_user)

@router.get("/performance")
def get_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get KPI metrics for the logged-in agent"""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=403, detail="Agent profile not found")
        
    return {
        "rating": agent.rating,
        "current_load": agent.current_load,
        "wallet_balance": agent.wallet_balance,
        "pending_earnings": agent.pending_earnings,
        "avg_response_time": agent.avg_response_time
    }

@router.get("/rankings", response_model=List[AgentResponse])
def get_agent_rankings(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN))
):
    """Public rankings for agents (Gamification)"""
    return db.query(Agent).order_by(Agent.rating.desc()).limit(10).all()

@router.post("/support")
def log_support(
    activity_type: str,
    farmer_id: uuid.UUID,
    notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log support and training activities performed by the agent"""
    return AgentService.log_support_activity(db, current_user, activity_type, farmer_id, notes)
