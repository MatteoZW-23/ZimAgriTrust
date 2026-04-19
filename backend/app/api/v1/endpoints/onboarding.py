from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.services.onboarding_service import OnboardingService
from app.schemas.onboarding import ContractSignRequest, QuizSubmission, ShadowingEvaluation, TrainingModuleResponse
from app.api.deps import require_roles, get_current_user, get_db
from app.models.user import User, UserRole
from app.models.onboarding import TrainingModule

router = APIRouter()

@router.post("/contract/{application_id}/sign")
def sign_contract(
    application_id: uuid.UUID,
    payload: ContractSignRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Digital signature for Agent Service Level Agreement"""
    ip = payload.ip_address or request.client.host
    return OnboardingService.sign_contract(db, application_id, payload.signee_name, payload.signature_data, ip)

@router.get("/academy/modules", response_model=List[TrainingModuleResponse])
def list_modules(db: Session = Depends(get_db)):
    """Retrieve catalog of training modules with quiz counts"""
    modules = db.query(TrainingModule).order_by(TrainingModule.order).all()
    # Dynamic count for the response model
    for m in modules:
        m.quiz_questions_count = len(m.quiz_data.get("questions", []))
    return modules

@router.post("/academy/{application_id}/quiz")
def submit_quiz(
    application_id: uuid.UUID,
    payload: QuizSubmission,
    db: Session = Depends(get_db)
):
    """Submit answers for an automated certification quiz"""
    return OnboardingService.submit_quiz(db, application_id, payload.module_id, payload.answers)

@router.post("/shadowing/{application_id}/evaluate", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def evaluate_shadowing(
    application_id: uuid.UUID,
    payload: ShadowingEvaluation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Senior agent evaluation of an applicant's field performance"""
    return OnboardingService.log_shadowing(db, application_id, current_user, payload.dict())

@router.get("/status/{application_id}")
def get_onboarding_status(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve detailed progress report for an agent in the onboarding pipeline"""
    return OnboardingService.get_onboarding_status(db, application_id)
