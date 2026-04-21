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
async def sign_contract(
    application_id: uuid.UUID,
    payload: ContractSignRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Digital signature for Agent Service Level Agreement"""
    ip = payload.ip_address or request.client.host
    return await OnboardingService.sign_contract(db, application_id, payload.signee_name, payload.signature_data, ip)

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

@router.post("/shadowing", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
async def log_shadowing(
    application_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    rating: float,
    db: Session = Depends(get_db)
):
    """Phase 5: Supervisor logs shading results"""
    from app.services.recruitment_service import RecruitmentService
    return await RecruitmentService.complete_shadowing(db, application_id, supervisor_id, rating)


@router.post("/shadowing/{application_id}/evaluate", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def evaluate_shadowing(
    application_id: uuid.UUID,
    payload: ShadowingEvaluation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Senior agent evaluation of an applicant's field performance"""
    return OnboardingService.log_shadowing(db, application_id, current_user, payload.dict())

from app.services.academy_service import academy_service
from app.models.recruitment import AgentApplication, ApplicationStatus

@router.get("/exam")
def get_certification_exam(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 6: Fetch randomized certification exam questions for an approved applicant"""
    application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found. Please verify your ID.")
    
    if application.status == ApplicationStatus.APPLIED:
        raise HTTPException(status_code=403, detail="Application Pending. Please wait for supervisor documentation approval before starting exams.")
    
    questions = academy_service.get_random_exam(10) # 10 questions for harder test
    # Hide correct answers before serving
    return [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in questions]

@router.post("/exam/submit")
def submit_certification_exam(
    application_id: uuid.UUID,
    answers: dict, # {question_id: selected_index}
    db: Session = Depends(get_db)
):
    """Phase 6: Self-mark exam and return results"""
    grade_report = academy_service.grade_exam(answers)
    
    if grade_report["passed"]:
        # Update training to 5/5 if they passed
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if application:
            # Step 5 Complete -> Move to Step 6: Practical Assessment (Master Plan)
            application.training_modules_completed = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "FINAL_EXAM"]
            application.status = ApplicationStatus.EXAM_PASSED
            db.commit()
            
    return grade_report

@router.get("/status/{application_id}")
def get_onboarding_status(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve detailed progress report for an agent in the onboarding pipeline"""
    return OnboardingService.get_onboarding_status(db, application_id)
