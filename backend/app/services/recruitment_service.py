from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime
from typing import List, Optional

from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentSpecialization
from app.schemas.recruitment import AgentApplicationCreate


class RecruitmentService:
    @staticmethod
    def submit_application(db: Session, payload: AgentApplicationCreate):
        existing = db.query(AgentApplication).filter(AgentApplication.national_id == payload.national_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Application already submitted for this ID")

        application = AgentApplication(**payload.model_dump())
        application.status = ApplicationStatus.DOCUMENTATION # Start documentation phase
        
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def complete_documentation(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        application.has_signed_contract = True
        application.id_verified = True
        application.payment_details_set = True
        application.status = ApplicationStatus.TRAINING
        db.commit()
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
            
        # Check if all 6 modules are complete
        if len(application.training_modules_completed) >= 6:
            application.status = ApplicationStatus.EQUIPMENT_SETUP
        
        db.commit()
        return application

    @staticmethod
    def setup_equipment(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application.equipment_issued = True
        application.app_configured = True
        application.status = ApplicationStatus.SHADOWING
        db.commit()
        return application

    @staticmethod
    def complete_shadowing(db: Session, application_id: uuid.UUID, supervisor_id: uuid.UUID, rating: float):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application.shadowing_supervisor_id = supervisor_id
        application.shadowing_rating = rating
        application.shadowing_tasks_completed = 20 # Requirement met
        application.status = ApplicationStatus.INDEPENDENT_SUPERVISED
        db.commit()
        return application

    @staticmethod
    def certify_agent(db: Session, application_id: uuid.UUID):
        application = db.query(AgentApplication).filter(AgentApplication.id == application_id).first()
        if not application:
             raise HTTPException(status_code=404, detail="Application not found")
        
        # 1. Create Formal Profiles
        from app.core.security import get_password_hash
        import random; import string
        temp_pin = ''.join(random.choices(string.digits, k=4))
        
        new_user = User(
            full_name=application.full_name,
            phone_number=application.phone_number,
            password_hash=get_password_hash(temp_pin),
            role=UserRole.AGENT,
            is_active=True,
            id_verified=True,
            trust_score=85
        )
        db.add(new_user)
        db.flush()

        agent = Agent(
            user_id=new_user.id,
            agent_code=f"AGT{str(uuid.uuid4())[:5]}".upper(),
            specialization=AgentSpecialization.ALL,
            province=application.province,
            district=application.district,
            status=AgentStatus.ACTIVE
        )
        db.add(agent)

        # 2. Finalize
        application.status = ApplicationStatus.CERTIFIED
        application.user_id = new_user.id
        application.reviewed_at = datetime.now()
        
        db.commit()
        return {"status": "certified", "agent_code": agent.agent_code, "temp_pin": temp_pin}
