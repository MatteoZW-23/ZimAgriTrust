from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.api.deps import get_db, require_roles, get_current_user
from app.services.agent_onboarding_service import agent_onboarding_service
from app.schemas.recruitment import AgentApplicationCreate, AgentApplicationResponse, TrainingUpdate
from app.models.user import User, UserRole
from app.models.recruitment import AgentApplication

router = APIRouter()

@router.get("/applications", response_model=List[AgentApplicationResponse], dependencies=[Depends(require_roles(UserRole.ADMIN))])
def list_applications(db: Session = Depends(get_db)):
    """Admin endpoint to view all agent applications in the pipeline"""
    return db.query(AgentApplication).all()

@router.post("/apply", response_model=AgentApplicationResponse)
async def submit_application(
    payload: AgentApplicationCreate,
    db: Session = Depends(get_db)
):
    """Public endpoint for new agent applicants - uses unified onboarding service"""
    return await agent_onboarding_service.submit_application(db, payload)

@router.get("/my-status/{phone_number}", response_model=AgentApplicationResponse)
def check_status(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Allow applicants to check their pipeline status via phone number"""
    app = db.query(AgentApplication).filter(AgentApplication.phone_number == phone_number).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.post("/{application_id}/documentation", response_model=AgentApplicationResponse, dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def verify_docs(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 1: Mark documentation and contracts as complete - uses unified onboarding service"""
    return await agent_onboarding_service.complete_documentation(db, application_id)

@router.post("/{application_id}/training/module/{module_id}")
async def complete_module(
    application_id: uuid.UUID,
    module_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Phase 2: Complete a specific training module - uses unified onboarding service"""
    return await agent_onboarding_service.complete_training_module(db, application_id, module_id)

@router.post("/{application_id}/equipment", dependencies=[Depends(require_roles(UserRole.ADMIN))])
def verify_equipment(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 3: Verify equipment issuance and app config - uses unified onboarding service"""
    return agent_onboarding_service.setup_equipment(db, application_id)

@router.post("/{application_id}/practical", dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def complete_practical(
    application_id: uuid.UUID,
    score: float,
    db: Session = Depends(get_db)
):
    """Phase 6: Record practical assessment score (Crop grading, app usage) - uses unified onboarding service"""
    return await agent_onboarding_service.complete_practical_assessment(db, application_id, score)

@router.post("/{application_id}/shadowing", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def complete_shadow(
    application_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    rating: float,
    db: Session = Depends(get_db)
):
    """Phase 7: Record shadowing results and supervisor sign-off - uses unified onboarding service"""
    return await agent_onboarding_service.complete_shadowing(db, application_id, supervisor_id, rating)

@router.post("/{application_id}/supervised-task", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def log_supervised_task(
    application_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Phase 8: Track supervised independent tasks (User needs 20 to pass) - uses unified onboarding service"""
    return await agent_onboarding_service.record_supervised_work(db, application_id)

@router.post("/{application_id}/certify", dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def certify_agent(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Phase 9: Final certification and account activation - uses unified onboarding service"""
    return await agent_onboarding_service.certify_agent(db, application_id)
