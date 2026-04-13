import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.listing import Listing
from app.models.dispute import Dispute
from app.models.agent import Agent, AgentAssignment
from app.schemas.agent import AgentResponse, AgentAssignmentResponse

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
        AgentAssignment.status.in_(["assigned", "in_progress"])
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

    assignment = db.query(AgentAssignment).filter(
        AgentAssignment.id == assignment_id,
        AgentAssignment.agent_id == agent.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.status = "in_progress"
    db.commit()
    return {"message": "Assignment accepted"}

@router.get("/rankings", response_model=List[AgentResponse])
def get_agent_rankings(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN))
):
    """Public rankings for agents (Gamification)"""
    return db.query(Agent).order_by(Agent.rating.desc(), Agent.total_verifications.desc()).limit(10).all()
