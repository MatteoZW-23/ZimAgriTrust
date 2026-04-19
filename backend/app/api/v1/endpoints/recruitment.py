from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.api.deps import get_db, require_roles, get_current_user
from app.services.recruitment_service import RecruitmentService
from app.schemas.recruitment import AgentApplicationCreate, AgentApplicationResponse, TrainingUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/applications", response_model=List[AgentApplicationResponse], dependencies=[Depends(require_roles(UserRole.ADMIN))])
def list_applications(db: Session = Depends(get_db)):
    """Admin endpoint to view all agent applications in the pipeline"""
    from app.models.recruitment import AgentApplication
    return db.query(AgentApplication).all()

@router.post("/apply", response_model=AgentApplicationResponse)
def submit_application(
    payload: AgentApplicationCreate,
    db: Session = Depends(get_db)
):
    """Public endpoint for new agent applicants"""
    return RecruitmentService.submit_application(db, payload)

@router.get("/my-status/{phone_number}", response_model=AgentApplicationResponse)
def check_status(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Allow applicants to check their pipeline status via phone number"""
    from app.models.recruitment import AgentApplication
    app = db.query(AgentApplication).filter(AgentApplication.phone_number == phone_number).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.post("/{application_id}/documentation", dependencies=[Depends(require_roles(UserRole.ADMIN))])
def verify_docs(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 1: Mark documentation and contracts as complete"""
    return RecruitmentService.complete_documentation(db, application_id)

@router.post("/{application_id}/training/module/{module_id}")
def complete_module(
    application_id: uuid.UUID,
    module_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Phase 2: Complete a specific training module"""
    return RecruitmentService.complete_training_module(db, application_id, module_id)

@router.post("/{application_id}/equipment", dependencies=[Depends(require_roles(UserRole.ADMIN))])
def verify_equipment(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 3: Verify equipment issuance and app config"""
    return RecruitmentService.setup_equipment(db, application_id)

@router.post("/{application_id}/shadowing", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def complete_shadow(
    application_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    rating: float,
    db: Session = Depends(get_db)
):
    """Phase 4: Record shadowing results and supervisor sign-off"""
    return RecruitmentService.complete_shadowing(db, application_id, supervisor_id, rating)

@router.post("/{application_id}/certify", dependencies=[Depends(require_roles(UserRole.ADMIN))])
def certify_agent(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Phase 5 & 6: Final certification and account activation"""
    return RecruitmentService.certify_agent(db, application_id)
