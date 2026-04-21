from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Float, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
import uuid
from datetime import datetime

class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    DOCS_VERIFIED = "DOCS_VERIFIED"
    TRAINING_PHASE_1 = "TRAINING_PHASE_1" # Modules 1-5
    EXAM_PASSED = "EXAM_PASSED" # Step 6
    READY_FOR_SHADOWING = "READY_FOR_SHADOWING" # Step 7
    SUPERVISED_INDEPENDENT = "SUPERVISED_INDEPENDENT" # Step 8
    READY_FOR_CERTIFICATION = "READY_FOR_CERTIFICATION" # Step 9
    CERTIFIED = "CERTIFIED" # Step 10
    REJECTED = "REJECTED"

class AgentApplication(Base):
    __tablename__ = "agent_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    full_name = Column(String(100))
    phone_number = Column(String(15), index=True)
    national_id = Column(String(20), unique=True)
    province = Column(String(50))
    district = Column(String(50))
    
    # Recruitment Profile (from Schema)
    has_smartphone = Column(Boolean, default=False)
    has_transport = Column(Boolean, default=False)
    transport_type = Column(String(50), nullable=True)
    agri_experience_years = Column(Integer, default=0)
    specializations = Column(JSON, default=[])

    status = Column(String, default=ApplicationStatus.APPLIED)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Progress tracking (AgriTrust 10-Step Pipeline)
    has_signed_contract = Column(Boolean, default=False)
    id_verified = Column(Boolean, default=False)
    
    # Training
    training_modules_completed = Column(JSON, default=[]) # List of module IDs
    
    # Equipment
    equipment_issued = Column(Boolean, default=False)
    
    # Practical/Shadowing
    shadowing_completed = Column(Boolean, default=False)
    shadowing_supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    shadowing_rating = Column(Float, nullable=True)
    
    # Supervised Work (Step 8)
    supervised_tasks_count = Column(Integer, default=0)
    
    # Final Review
    reviewer_notes = Column(JSON, default=[])
    reviewed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="application", foreign_keys=[user_id])
