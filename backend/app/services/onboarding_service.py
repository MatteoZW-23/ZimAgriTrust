from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict

from app.models.onboarding import AgentContract, TrainingModule, AgentTrainingProgress, ShadowingLog, OnboardingPhase
from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.user import User


class OnboardingService:
    @staticmethod
    async def sign_contract(db: Session, application_id: uuid.UUID, signee_name: str, signature_data: str, ip: str):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate integrity hash
        content_source = f"{application_id}-{signee_name}-{datetime.now(timezone.utc).isoformat()}"
        integrity_hash = hashlib.sha256(content_source.encode()).hexdigest()

        contract = AgentContract(
            application_id=application_id,
            signed_by_name=signee_name,
            signature_base64=signature_data,
            ip_address=ip,
            content_hash=integrity_hash
        )
        db.add(contract)
        
        # Advance phase to Phase 3: Curriculum (Master Plan)
        application.status = ApplicationStatus.TRAINING_PHASE_1
        
        # Notify Applicant
        from app.services.whatsapp_service import WhatsAppService
        msg = (
            f"✍️ *Contract Signed Successfully*\n\n"
            f"Your Agent SLA has been digitally signed and archived.\n\n"
            f"You are now enrolled in the Academy. Please log in to the Training Portal using your ID: *{application_id}*"
        )
        await WhatsAppService.send_whatsapp_message(application.phone_number, msg)
        
        db.commit()
        return contract

    @staticmethod
    def submit_quiz(db: Session, application_id: uuid.UUID, module_id: uuid.UUID, answers: Dict[str, str]):
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
             raise HTTPException(status_code=404, detail="Module not found")

        # Basic Scoring Logic
        correct_count = 0
        total_questions = len(module.quiz_data.get("questions", []))
        
        for q in module.quiz_data.get("questions", []):
            q_id = q.get("id")
            if answers.get(q_id) == q.get("correct_answer"):
                correct_count += 1
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Update Progress
        progress = db.query(AgentTrainingProgress).filter(
            AgentTrainingProgress.application_id == application_id,
            AgentTrainingProgress.module_id == module_id
        ).first()
        
        if not progress:
            progress = AgentTrainingProgress(application_id=application_id, module_id=module_id)
            db.add(progress)
        
        progress.quiz_score = score
        progress.attempts += 1
        if score >= module.min_pass_score:
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
            
        db.commit()
        return {"score": score, "passed": score >= module.min_pass_score}

    @staticmethod
    def log_shadowing(db: Session, application_id: uuid.UUID, supervisor: User, rubric: Dict):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        log = ShadowingLog(
            application_id=application_id,
            supervisor_id=supervisor.id,
            technical_accuracy=rubric.get("technical_accuracy", 1),
            professionalism=rubric.get("professionalism", 1),
            communication=rubric.get("communication", 1),
            reviewer_notes=rubric.get("notes"),
            recommendation=rubric.get("recommendation", "ready")
        )
        db.add(log)
        
        if log.recommendation == "ready":
             application.status = ApplicationStatus.SUPERVISED_INDEPENDENT
        
        db.commit()
        return log

    @staticmethod
    def get_onboarding_status(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Calculate percentage complete
        phases = list(OnboardingPhase)
        try:
            current_idx = phases.index(application.status.value)
        except ValueError:
            current_idx = 0
            
        progress_per = (current_idx / len(phases)) * 100
        
        # Modules detail
        modules = db.query(AgentTrainingProgress).filter(AgentTrainingProgress.application_id == application_id).all()
        
        return {
            "full_name": application.full_name,
            "status": application.status,
            "overall_progress_percent": round(progress_per, 2),
            "documentation_complete": application.has_signed_contract,
            "training_modules_completed_count": len([m for m in modules if m.status == "completed"]),
            "equipment_setup_complete": application.equipment_issued,
            "shadowing_tasks_count": application.shadowing_tasks_completed
        }
