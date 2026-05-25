"""
Unified Agent Onboarding Service

This service consolidates the functionality from recruitment_service.py and onboarding_service.py
into a single, coherent onboarding pipeline for agents.

It combines:
- Pipeline orchestration from recruitment_service
- Detailed task execution from onboarding_service (contracts, quizzes, shadowing evaluations)
- Single source of truth for status (ApplicationStatus)
- Enhanced data tracking with detailed records
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
import hashlib
import random
import string
from datetime import datetime, timezone
from typing import List, Optional, Dict

from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentStatus, AgentSpecialization
from app.models.academy import AgentTraining
from app.models.onboarding import AgentContract, TrainingModule, AgentTrainingProgress, ShadowingLog
from app.schemas.recruitment import AgentApplicationCreate
from app.core.security import get_password_hash
from app.services.whatsapp_service import WhatsAppService


class AgentOnboardingService:
    """Unified service for agent onboarding and recruitment pipeline."""
    
    @staticmethod
    async def submit_application(db: Session, payload: AgentApplicationCreate) -> AgentApplication:
        """
        Step 1: Submit initial agent application.
        
        Creates an AgentApplication record with status APPLIED.
        """
        existing = db.query(AgentApplication).filter(
            AgentApplication.national_id == payload.national_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Application already submitted for this ID"
            )

        application = AgentApplication(**payload.model_dump())
        application.status = ApplicationStatus.APPLIED
        application.full_name = f"{payload.first_name} {payload.last_name}"
        
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    async def complete_documentation(
        db: Session, 
        application_id: uuid.UUID,
        sign_contract: bool = False,
        signee_name: Optional[str] = None,
        signature_data: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AgentApplication:
        """
        Step 2: Verify documentation and optionally sign contract.
        
        Verifies applicant documents, creates trainee account, initializes academy progress,
        and optionally handles digital contract signing.
        
        This method combines functionality from:
        - recruitment_service.complete_documentation()
        - onboarding_service.sign_contract()
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if not application.phone_number:
            raise HTTPException(
                status_code=400, 
                detail="Applicant phone number is missing"
            )

        # Handle contract signing if provided
        if sign_contract and signee_name and signature_data:
            await AgentOnboardingService._sign_contract_internal(
                db, application, signee_name, signature_data, ip_address
            )
        else:
            # Mark contract as signed for legacy compatibility
            application.has_signed_contract = True

        application.id_verified = True
        application.status = ApplicationStatus.DOCS_VERIFIED
        
        # Provision trainee account
        temp_pin = ''.join(random.choices(string.digits, k=6))
        user = await AgentOnboardingService._provision_trainee_account(
            db, application, temp_pin
        )

        # Create trainee agent record
        agent = await AgentOnboardingService._create_trainee_agent(
            db, user, application, temp_pin
        )

        # Initialize academy progress
        await AgentOnboardingService._initialize_academy_progress(db, agent)

        # Notify applicant
        await AgentOnboardingService._send_documentation_notification(
            application, agent.agent_code, temp_pin
        )
        
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    async def _sign_contract_internal(
        db: Session,
        application: AgentApplication,
        signee_name: str,
        signature_data: str,
        ip: str
    ) -> AgentContract:
        """Internal method to handle contract signing."""
        content_source = f"{application.id}-{signee_name}-{datetime.now(timezone.utc).isoformat()}"
        integrity_hash = hashlib.sha256(content_source.encode()).hexdigest()

        contract = AgentContract(
            application_id=application.id,
            signed_by_name=signee_name,
            signature_base64=signature_data,
            ip_address=ip,
            content_hash=integrity_hash
        )
        db.add(contract)
        
        application.has_signed_contract = True
        
        return contract

    @staticmethod
    async def _provision_trainee_account(
        db: Session,
        application: AgentApplication,
        temp_pin: str
    ) -> User:
        """Provision or update trainee user account."""
        hashed_pin = get_password_hash(temp_pin)
        
        # Check if user already exists
        user = db.query(User).filter(
            User.phone_number == application.phone_number
        ).first()
        
        if not user:
            user = User(
                full_name=application.full_name,
                phone_number=application.phone_number,
                password_hash=hashed_pin,
                ussd_pin_hash=hashed_pin,
                role=UserRole.AGENT,
                is_active=True,
                id_verified=True,
                trust_score=85,
                must_change_password=True,
            )
            db.add(user)
            db.flush()
        else:
            if user.role != UserRole.ADMIN:
                user.role = UserRole.AGENT
            user.id_verified = True
            user.password_hash = hashed_pin
            user.ussd_pin_hash = hashed_pin
            user.must_change_password = True
        
        return user

    @staticmethod
    async def _create_trainee_agent(
        db: Session,
        user: User,
        application: AgentApplication,
        temp_pin: str
    ) -> Agent:
        """Create trainee agent record."""
        from app.core.security import get_password_hash
        
        agent = db.query(Agent).filter(Agent.user_id == user.id).first()
        if not agent:
            agent = Agent(
                user_id=user.id,
                agent_code=f"TRN{str(uuid.uuid4())[:5]}".upper(),
                pin_hash=get_password_hash(temp_pin),
                specialization=AgentSpecialization.FIELD_SUPPORT,
                province=application.province,
                district=application.district,
                status=AgentStatus.TRAINEE
            )
            db.add(agent)
            db.flush()
        
        return agent

    @staticmethod
    async def _initialize_academy_progress(db: Session, agent: Agent) -> AgentTraining:
        """Initialize academy training progress."""
        training = db.query(AgentTraining).filter(
            AgentTraining.agent_id == agent.id
        ).first()
        if not training:
            training = AgentTraining(agent_id=agent.id)
            db.add(training)
        
        return training

    @staticmethod
    async def _send_documentation_notification(
        application: AgentApplication,
        agent_code: str,
        temp_pin: str
    ):
        """Send WhatsApp notification for documentation approval."""
        msg = (
            f"✅ *ZimAgritrust Documentation Approved*\n\n"
            f"Welcome to the pipeline, {application.full_name}. "
            f"Your documentation has been verified.\n\n"
            f"Your Trainee Account is ready:\n"
            f"🆔 *Agent Code:* {agent_code}\n"
            f"🔑 *Initial PIN:* {temp_pin}\n\n"
            f"Login to the Agent Academy and begin your certification process."
        )
        try:
            await WhatsAppService.send_whatsapp_message(
                application.phone_number, msg
            )
        except Exception as e:
            import logging
            logging.error(f"WhatsApp Notification Failed (Non-critical): {e}")

    @staticmethod
    async def complete_training_module(
        db: Session,
        application_id: uuid.UUID,
        module_id: str,
        answers: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Step 3-5: Complete training module with optional quiz submission.
        
        This method combines:
        - recruitment_service.complete_training_module() (simple tracking)
        - onboarding_service.submit_quiz() (detailed quiz scoring)
        
        If answers are provided, uses detailed quiz scoring.
        Otherwise, uses simple module completion tracking.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        result = {}
        
        if answers:
            # Use detailed quiz scoring
            result = await AgentOnboardingService._submit_quiz_internal(
                db, application_id, module_id, answers
            )
        else:
            # Use simple completion tracking
            if module_id not in application.training_modules_completed:
                modules = list(application.training_modules_completed)
                modules.append(module_id)
                application.training_modules_completed = modules
            result = {"completed": True, "score": None}
        
        db.commit()
        return result

    @staticmethod
    async def _submit_quiz_internal(
        db: Session,
        application_id: uuid.UUID,
        module_id: str,
        answers: Dict[str, str]
    ) -> Dict:
        """Internal method for detailed quiz scoring."""
        # Try to get module by ID or name
        try:
            module_uuid = uuid.UUID(module_id)
            module = db.query(TrainingModule).filter(
                TrainingModule.id == module_uuid
            ).first()
        except ValueError:
            # Try to find by module identifier/name
            module = db.query(TrainingModule).filter(
                TrainingModule.identifier == module_id
            ).first()
        
        if not module:
            # Fallback: just mark as completed
            application = db.query(AgentApplication).filter(
                AgentApplication.id == application_id
            ).first()
            if module_id not in application.training_modules_completed:
                modules = list(application.training_modules_completed)
                modules.append(module_id)
                application.training_modules_completed = modules
            return {"completed": True, "score": None, "passed": True}

        # Scoring logic
        correct_count = 0
        total_questions = len(module.quiz_data.get("questions", []))
        
        for q in module.quiz_data.get("questions", []):
            q_id = q.get("id")
            if answers.get(q_id) == q.get("correct_answer"):
                correct_count += 1
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Update progress
        progress = db.query(AgentTrainingProgress).filter(
            AgentTrainingProgress.application_id == application_id,
            AgentTrainingProgress.module_id == module.id
        ).first()
        
        if not progress:
            progress = AgentTrainingProgress(
                application_id=application_id,
                module_id=module.id
            )
            db.add(progress)
        
        progress.quiz_score = score
        progress.attempts += 1
        
        passed = False
        if score >= (module.min_pass_score or 70):
            progress.status = "completed"
            progress.completed_at = datetime.now(timezone.utc)
            passed = True
            
            # Also update legacy tracking
            application = db.query(AgentApplication).filter(
                AgentApplication.id == application_id
            ).first()
            if module_id not in application.training_modules_completed:
                modules = list(application.training_modules_completed)
                modules.append(module_id)
                application.training_modules_completed = modules
        
        return {
            "score": score,
            "passed": passed,
            "completed": passed
        }

    @staticmethod
    def setup_equipment(db: Session, application_id: uuid.UUID) -> AgentApplication:
        """
        Step 6: Issue equipment to agent.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application.equipment_issued = True
        application.status = ApplicationStatus.READY_FOR_SHADOWING
        db.commit()
        return application

    @staticmethod
    async def complete_practical_assessment(
        db: Session,
        application_id: uuid.UUID,
        score: float
    ) -> AgentApplication:
        """
        Step 6: Record practical assessment score.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application.reviewed_at = datetime.now()
        application.reviewer_notes = f"Practical Assessment Score: {score}%"
        
        if score >= 80:
            application.status = ApplicationStatus.READY_FOR_SHADOWING
        
        db.commit()
        return application

    @staticmethod
    async def complete_shadowing(
        db: Session,
        application_id: uuid.UUID,
        supervisor_id: uuid.UUID,
        rating: Optional[float] = None,
        rubric: Optional[Dict] = None
    ) -> AgentApplication:
        """
        Step 7: Complete shadowing phase.
        
        This method combines:
        - recruitment_service.complete_shadowing() (simple rating)
        - onboarding_service.log_shadowing() (detailed rubric)
        
        If rubric is provided, uses detailed evaluation.
        Otherwise, uses simple rating.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if rubric:
            # Use detailed rubric evaluation
            await AgentOnboardingService._log_shadowing_internal(
                db, application_id, supervisor_id, rubric
            )
            
            # Check if ready to advance
            if rubric.get("recommendation") == "ready":
                application.shadowing_supervisor_id = supervisor_id
                application.shadowing_rating = rubric.get("technical_accuracy", rating or 5)
                application.shadowing_completed = True
                application.status = ApplicationStatus.SUPERVISED_INDEPENDENT
        else:
            # Use simple rating
            application.shadowing_supervisor_id = supervisor_id
            application.shadowing_rating = rating or 5
            application.shadowing_completed = True
            application.status = ApplicationStatus.SUPERVISED_INDEPENDENT
        
        # Notify applicant
        msg = (
            f"🌟 *Shadowing Phase Complete*\n\n"
            f"Well done, {application.full_name}! Your shadowing supervisor has signed off on your field performance.\n\n"
            f"You are now entering the Supervised Independence phase (Step 8)."
        )
        await WhatsAppService.send_whatsapp_message(application.phone_number, msg)
        
        db.commit()
        return application

    @staticmethod
    async def _log_shadowing_internal(
        db: Session,
        application_id: uuid.UUID,
        supervisor_id: uuid.UUID,
        rubric: Dict
    ) -> ShadowingLog:
        """Internal method for detailed shadowing evaluation."""
        log = ShadowingLog(
            application_id=application_id,
            supervisor_id=supervisor_id,
            technical_accuracy=rubric.get("technical_accuracy", 1),
            professionalism=rubric.get("professionalism", 1),
            communication=rubric.get("communication", 1),
            reviewer_notes=rubric.get("notes"),
            recommendation=rubric.get("recommendation", "ready")
        )
        db.add(log)
        return log

    @staticmethod
    async def record_supervised_work(
        db: Session,
        application_id: uuid.UUID
    ) -> AgentApplication:
        """
        Step 8: Record supervised independent work task.
        
        User needs 20 tasks to pass Step 8.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application.supervised_tasks_count += 1
        
        if application.supervised_tasks_count >= 20:
            application.status = ApplicationStatus.READY_FOR_CERTIFICATION
            
        db.commit()
        return application

    @staticmethod
    async def certify_agent(
        db: Session,
        application_id: uuid.UUID
    ) -> Dict:
        """
        Step 9: Final certification.
        
        Upgrades agent from trainee to active status.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Ensure agent record exists and upgrade status
        agent = db.query(Agent).filter(
            Agent.user_id == application.user_id
        ).first()
        
        if not agent:
            # Create agent record if missing
            user = db.query(User).filter(
                User.id == application.user_id
            ).first()
            if not user:
                raise HTTPException(
                    status_code=404, 
                    detail="User not found for this application"
                )
            
            agent = Agent(
                user_id=user.id,
                agent_code=f"AGT{str(uuid.uuid4())[:5]}".upper(),
                status=AgentStatus.ACTIVE,
                province=application.province,
                district=application.district,
                specialization=AgentSpecialization.FIELD_SUPPORT
            )
            db.add(agent)
            application.user_id = user.id
            db.flush()
        else:
            agent.status = AgentStatus.ACTIVE
            # Promote code prefix from TRN to AGT
            if agent.agent_code.startswith("TRN"):
                agent.agent_code = agent.agent_code.replace("TRN", "AGT")
        
        # Finalize application
        application.status = ApplicationStatus.CERTIFIED
        application.reviewed_at = datetime.now()
        
        # Send congratulations notification
        msg = (
            f"🎓 *Congratulations, Agent!*\n\n"
            f"You are now a certified ZimAgritrust Regional Node.\n\n"
            f"🆔 *Agent Code:* {agent.agent_code}\n\n"
            f"You have full access to the Field Portal."
        )
        await WhatsAppService.send_whatsapp_message(application.phone_number, msg)
        
        # Audit log
        from app.models.audit_log import AuditLog
        audit = AuditLog(
            action="AGENT_CERTIFICATION",
            resource_type="AGENT",
            resource_id=str(agent.id),
            details={
                "application_id": str(application_id),
                "agent_code": agent.agent_code,
                "province": application.province
            }
        )
        db.add(audit)
        
        db.commit()
        return {
            "status": "certified",
            "agent_code": agent.agent_code
        }

    @staticmethod
    def get_application_status(
        db: Session,
        user_id: uuid.UUID
    ) -> Dict:
        """Get current application status for a user."""
        application = db.query(AgentApplication).filter(
            AgentApplication.user_id == user_id
        ).first()
        if not application:
            return {"status": "NOT_FOUND", "step": 0}
        
        return {
            "application_id": str(application.id),
            "status": application.status.value,
            "full_name": application.full_name,
            "step": AgentOnboardingService._get_step_from_status(application.status)
        }

    @staticmethod
    def get_onboarding_status(
        db: Session,
        application_id: uuid.UUID
    ) -> Dict:
        """
        Get detailed onboarding progress.
        
        Combines status tracking from both services.
        """
        application = db.query(AgentApplication).filter(
            AgentApplication.id == application_id
        ).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Calculate progress percentage
        step = AgentOnboardingService._get_step_from_status(application.status)
        progress_percent = (step / 9) * 100  # 9 steps total
        
        # Get detailed module progress
        modules = db.query(AgentTrainingProgress).filter(
            AgentTrainingProgress.application_id == application_id
        ).all()
        
        # Get shadowing logs
        shadowing_logs = db.query(ShadowingLog).filter(
            ShadowingLog.application_id == application_id
        ).all()
        
        return {
            "application_id": str(application_id),
            "full_name": application.full_name,
            "status": application.status.value,
            "current_step": step,
            "overall_progress_percent": round(progress_percent, 2),
            "documentation_complete": application.has_signed_contract,
            "contract_signed": bool(db.query(AgentContract).filter(
                AgentContract.application_id == application_id
            ).first()),
            "training_modules_completed_count": len(
                [m for m in modules if m.status == "completed"]
            ),
            "training_modules_total": len(modules),
            "equipment_setup_complete": application.equipment_issued,
            "shadowing_completed": application.shadowing_completed,
            "shadowing_rating": application.shadowing_rating,
            "shadowing_logs_count": len(shadowing_logs),
            "supervised_tasks_count": application.supervised_tasks_count,
            "supervised_tasks_required": 20,
            "certified": application.status == ApplicationStatus.CERTIFIED
        }

    @staticmethod
    def _get_step_from_status(status: ApplicationStatus) -> int:
        """Map ApplicationStatus to step number (1-9)."""
        step_mapping = {
            ApplicationStatus.APPLIED: 1,
            ApplicationStatus.DOCS_VERIFIED: 2,
            ApplicationStatus.TRAINING_PHASE_1: 3,
            ApplicationStatus.TRAINING_PHASE_2: 4,
            ApplicationStatus.TRAINING_PHASE_3: 5,
            ApplicationStatus.READY_FOR_SHADOWING: 6,
            ApplicationStatus.SUPERVISED_INDEPENDENT: 8,
            ApplicationStatus.READY_FOR_CERTIFICATION: 9,
            ApplicationStatus.CERTIFIED: 10,
        }
        return step_mapping.get(status, 0)


# Singleton instance
agent_onboarding_service = AgentOnboardingService()
