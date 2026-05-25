import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.academy import AgentTraining, AcademyModule, ExamAttempt, ModuleStatus, CertificationLevel

router = APIRouter()

class FieldTrainingUpdate(BaseModel):
    shadowing_tasks: Optional[int] = None
    supervised_tasks: Optional[int] = None
    field_score: Optional[float] = None
    certification_level: Optional[str] = None

@router.get("/progress")
def list_all_agent_progress(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN))
):
    """View training progress for all agent candidates"""
    progress = db.query(AgentTraining).options(joinedload(AgentTraining.agent)).all()
    
    return [
        {
            "agent_id": str(p.agent_id),
            "agent_name": p.agent.user.full_name if p.agent.user else "Unknown",
            "certification_level": p.certification_level.value if p.certification_level else CertificationLevel.TRAINEE.value,
            "modules_completed": sum([
                1 for i in range(1, 11) if getattr(p, f"module_{i}_status") == ModuleStatus.COMPLETED
            ]),
            "final_exam_score": p.final_exam_score,
            "field_score": p.field_evaluation_score,
            "updated_at": p.updated_at
        }
        for p in progress
    ]

@router.get("/progress/{agent_id}")
def get_agent_detailed_progress(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN))
):
    """Detailed view of a single agent's training record"""
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training record not found")
        
    return training

@router.post("/progress/{agent_id}/field-training")
def update_field_training(
    agent_id: uuid.UUID,
    update: FieldTrainingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN))
):
    """Manually update field training metrics (shadowing, supervised tasks)"""
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Training record not found")

    if update.shadowing_tasks is not None:
        training.shadowing_tasks_completed = update.shadowing_tasks
    if update.supervised_tasks is not None:
        training.supervised_tasks_completed = update.supervised_tasks
    if update.field_score is not None:
        training.field_evaluation_score = update.field_score
    if update.certification_level is not None:
        try:
            training.certification_level = CertificationLevel(update.certification_level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid certification_level: {update.certification_level}")

    db.commit()
    return {"message": "Field training progress updated"}

@router.get("/modules")
def list_training_modules(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN))
):
    """View and manage academic curriculum modules"""
    return db.query(AcademyModule).order_by(AcademyModule.order).all()
