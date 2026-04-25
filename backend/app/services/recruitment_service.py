from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime
from typing import List, Optional

from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentSpecialization
from app.schemas.recruitment import AgentApplicationCreate


from app.services.whatsapp_service import WhatsAppService


class RecruitmentService:
    @staticmethod
    async def submit_application(db: Session, payload: AgentApplicationCreate):
        existing = db.query(AgentApplication).filter(AgentApplication.national_id == payload.national_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Application already submitted for this ID")

        application = AgentApplication(**payload.model_dump())
        application.status = ApplicationStatus.APPLIED
        
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    async def complete_documentation(db: Session, application_id: uuid.UUID):
        """
        Phase 1: Verify documentation and prepare the trainee account.
        This method is now hardened to prevent null-reference crashes and 
        ensures the academy progress is initialized.
        """
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        if not application.phone_number:
             raise HTTPException(status_code=400, detail="Applicant phone number is missing")

        application.has_signed_contract = True
        application.id_verified = True
        application.status = ApplicationStatus.DOCS_VERIFIED
        
        # PROVISION TRAINEE ACCOUNT
        from app.core.security import get_password_hash
        from app.models.agent import Agent, AgentStatus, AgentSpecialization
        from app.models.academy import AgentTraining
        from app.services.whatsapp_service import whatsapp_service
        import random, string
        
        # Check if user already exists
        user = db.query(User).filter(User.phone_number == application.phone_number).first()
        temp_pin = ''.join(random.choices(string.digits, k=6))
        
        if not user:
            hashed_pin = get_password_hash(temp_pin)
            user = User(
                full_name=application.full_name,
                phone_number=application.phone_number,
                password_hash=hashed_pin,
                ussd_pin_hash=hashed_pin,
                role=UserRole.AGENT,
                is_active=True,
                id_verified=True,
                trust_score=85,
                must_change_password=True,  # Force PIN change on first login
            )
            db.add(user)
            db.flush()
        else:
            if user.role != UserRole.ADMIN: # Don't downgrade admins
                user.role = UserRole.AGENT
            user.id_verified = True
            # Always sync the PIN so the WhatsApp message matches what's stored
            hashed_pin = get_password_hash(temp_pin)
            user.password_hash = hashed_pin
            user.ussd_pin_hash = hashed_pin
            user.must_change_password = True  # Force PIN change on first login

        # Create Trainee Agent record
        agent = db.query(Agent).filter(Agent.user_id == user.id).first()
        if not agent:
            agent = Agent(
                user_id=user.id,
                agent_code=f"TRN{str(uuid.uuid4())[:5]}".upper(),
                specialization=AgentSpecialization.FIELD_SUPPORT,
                province=application.province,
                district=application.district,
                status=AgentStatus.TRAINEE
            )
            db.add(agent)
            db.flush()

        # Initialize Academy Progress (Step 2-5 Foundation)
        training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent.id).first()
        if not training:
            training = AgentTraining(agent_id=agent.id)
            db.add(training)

        application.user_id = user.id

        # Notify Applicant (WhatsApp Bridge) - Resilient to bridge downtime
        msg = (
            f"✅ *AgriTrust Documentation Approved*\n\n"
            f"Welcome to the pipeline, {application.full_name}. Your documentation has been verified.\n\n"
            f"Your Trainee Account is ready:\n"
            f"🆔 *Agent Code:* {agent.agent_code}\n"
            f"🔑 *Initial PIN:* {temp_pin}\n\n"
            f"Login to the Agent Academy and begin your certification process."
        )
        try:
            await whatsapp_service.send_whatsapp_message(application.phone_number, msg)
        except Exception as e:
            import logging
            logging.error(f"WhatsApp Notification Failed (Non-critical): {e}")
        
        db.commit()
        db.refresh(application)
        return application


    @staticmethod
    def complete_training_module(db: Session, application_id: uuid.UUID, module_id: str):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if module_id not in application.training_modules_completed:
            modules = list(application.training_modules_completed)
            modules.append(module_id)
            application.training_modules_completed = modules
        
        db.commit()
        return application

    @staticmethod
    def setup_equipment(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application.equipment_issued = True
        application.status = ApplicationStatus.READY_FOR_SHADOWING
        db.commit()
        return application

    @staticmethod
    async def complete_shadowing(db: Session, application_id: uuid.UUID, supervisor_id: uuid.UUID, rating: float):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application.shadowing_supervisor_id = supervisor_id
        application.shadowing_rating = rating
        application.shadowing_completed = True
        application.status = ApplicationStatus.SUPERVISED_INDEPENDENT # Move to Step 8
        
        # Notify Applicant
        msg = (
            f"🌟 *Shadowing Phase Complete*\n\n"
            f"Well done, {application.full_name}! Your shadowing supervisor has signed off on your field performance (Rating: {rating}/5).\n\n"
            f"You are now entering the Supervised Independence phase (Step 8)."
        )
        await WhatsAppService.send_whatsapp_message(application.phone_number, msg)
        
        db.commit()
        return application

    @staticmethod
    async def complete_practical_assessment(db: Session, application_id: uuid.UUID, score: float):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        application.reviewed_at = datetime.now()
        application.reviewer_notes = f"Practical Assessment Score: {score}%"
        
        if score >= 80: # Requirement matches exam passing threshold
            application.status = ApplicationStatus.READY_FOR_SHADOWING # Move to Phase 7
        
        db.commit()
        return application

    @staticmethod
    async def record_supervised_work(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        application.supervised_tasks_count += 1
        
        # User needs 20 tasks to pass Step 8 as per Master Plan
        if application.supervised_tasks_count >= 20:
            application.status = ApplicationStatus.READY_FOR_CERTIFICATION # Move to Step 9
            
        db.commit()
        return application

    @staticmethod
    async def certify_agent(db: Session, application_id: uuid.UUID):
        from app.models.agent import AgentStatus
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        # 1. Update/Provision Trainee Profile (Self-Healing)
        from app.models.agent import Agent, AgentStatus, AgentSpecialization
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        import random, string

        agent = db.query(Agent).filter(Agent.user_id == application.user_id).first()
        if not agent:
             # Check if user exists but just has no agent record
             user = db.query(User).filter(User.phone_number == application.phone_number).first()
             if not user:
                 temp_pin = ''.join(random.choices(string.digits, k=6))
                 hashed_pin = get_password_hash(temp_pin)
                 user = User(
                     full_name=application.full_name,
                     phone_number=application.phone_number,
                     password_hash=hashed_pin,
                     ussd_pin_hash=hashed_pin,
                     role=UserRole.AGENT,
                     is_active=True,
                     id_verified=True
                 )
                 db.add(user)
                 db.flush()
             
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
            agent.agent_code = agent.agent_code.replace("TRN", "AGT") # Promote code prefix

        
        # 2. Finalize
        application.status = ApplicationStatus.CERTIFIED
        application.reviewed_at = datetime.now()
        
        # 3. WhatsApp Notification
        msg = (
            f"🎓 *Congratulations, Agent!*\n\n"
            f"You are now a certified AgriTrust Regional Node.\n\n"
            f"🆔 *Agent Code:* {agent.agent_code}\n\n"
            f"You have full access to the Field Portal."
        )
        await WhatsAppService.send_whatsapp_message(application.phone_number, msg)
        
        # 4. Global Audit Log
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
        return {"status": "certified", "agent_code": agent.agent_code}


    @staticmethod
    def get_application_status(db: Session, user_id: int):
        from app.models.recruitment import AgentApplication
        application = db.query(AgentApplication).filter(AgentApplication.user_id == user_id).first()
        if not application:
            return {"status": "NOT_FOUND", "step": 0}
        return {
            "application_id": application.id,
            "status": application.status,
            "full_name": application.full_name
        }

recruitment_service = RecruitmentService()
