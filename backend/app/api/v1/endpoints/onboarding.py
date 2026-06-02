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

from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.classroom import Resource, ResourceType, QuizQuestion, QuizAttempt, Enrollment
from app.models.agent import AgentStatus, Agent
from app.models.onboarding import AgentTrainingProgress
from datetime import datetime, timezone, timedelta
import random
import hashlib

@router.get("/exam")
def get_certification_exam(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Phase 6: Fetch randomized certification exam questions for an approved applicant"""
    application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found. Please verify your ID.")
    
    if application.status == ApplicationStatus.APPLIED:
        raise HTTPException(status_code=403, detail="Application Pending. Please wait for supervisor documentation approval before starting exams.")
    
    quiz_resources = db.query(Resource).filter(Resource.resource_type == ResourceType.QUIZ).all()
    if not quiz_resources:
        raise HTTPException(status_code=404, detail="No published academy exam configured")
    pool = []
    for r in quiz_resources:
        for q in db.query(QuizQuestion).filter(QuizQuestion.resource_id == r.id).all():
            pool.append({"resource_id": r.id, "question": q})
    random.shuffle(pool)
    selected = pool[: min(200, len(pool))]
    if len(selected) == 0:
        raise HTTPException(status_code=400, detail="Question bank is empty")

    attempt = QuizAttempt(
        enrollment_id=db.query(Enrollment).filter(Enrollment.agent_id == application.agent_id).first().id if application.agent_id else None,
        resource_id=selected[0]["resource_id"],
        answers={"exam_session": hashlib.sha256(f"{application_id}-{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()},
        started_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        "attempt_id": str(attempt.id),
        "duration_minutes": 60,
        "max_attempts": 2,
        "pass_mark": 80,
        "questions": [{"id": str(x["question"].id), "question": x["question"].question_text, "options": x["question"].options, "type": x["question"].question_type.value} for x in selected]
    }

@router.post("/exam/submit")
def submit_certification_exam(
    application_id: uuid.UUID,
    answers: dict, # {question_id: selected_index}
    db: Session = Depends(get_db)
):
    """Phase 6: Self-mark exam and return results"""
    application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    training = db.query(AgentTrainingProgress).filter(AgentTrainingProgress.application_id == application.id).first()
    if not training:
        training = AgentTrainingProgress(application_id=application.id, status="in_progress")
        db.add(training)
        db.flush()
    training.final_exam_attempts = (training.final_exam_attempts or 0) + 1
    score = float(answers.get("score", 0))
    passed = score >= 80.0
    training.final_exam_score = score
    if passed:
        now = datetime.now(timezone.utc)
        training.certification_status = "certified"
        training.certification_level = "CERTIFIED"
        training.certification_issued_at = now
        training.certification_expires_at = now + timedelta(days=365)
        training.certificate_id = f"ZAT-CERT-{str(application.id)[:8].upper()}"
        training.qr_verification_code = hashlib.sha256(training.certificate_id.encode()).hexdigest()
        training.review_required = False
        application.status = ApplicationStatus.EXAM_PASSED
        if application.user_id:
            agent = db.query(Agent).filter(Agent.user_id == application.user_id).first()
            if agent:
                agent.status = AgentStatus.ACTIVE
    elif training.final_exam_attempts >= 2:
        training.review_required = True
        training.certification_status = "review_required"
    db.commit()
    return {"passed": passed, "score": score, "attempts": training.final_exam_attempts, "status": training.certification_status}

@router.get("/status/{application_id}")
def get_onboarding_status(application_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve detailed progress report for an agent in the onboarding pipeline"""
    return OnboardingService.get_onboarding_status(db, application_id)
