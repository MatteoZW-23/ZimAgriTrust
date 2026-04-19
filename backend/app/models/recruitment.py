import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    EQUIPMENT_SETUP = "equipment_setup"
    SHADOWING = "shadowing"
    INDEPENDENT_SUPERVISED = "independent_supervised"
    CERTIFIED = "certified"
    REJECTED = "rejected"


class AgentApplication(Base) :
    __tablename__ = "agent_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Candidate Info
    full_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(20), index=True)
    national_id: Mapped[str] = mapped_column(String(50), unique=True)
    province: Mapped[str] = mapped_column(String(50))
    district: Mapped[str] = mapped_column(String(50))
    
    # Progress Tracking (Phases)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    
    # Phase 1: Documentation
    has_signed_contract: Mapped[bool] = mapped_column(Boolean, default=False)
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_details_set: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Phase 2: Training
    training_modules_completed: Mapped[List[str]] = mapped_column(JSON, default=list) # ["module1", "module2"]
    certification_exam_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Phase 3: Equipment
    equipment_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    app_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Phase 4: Shadowing
    shadowing_tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    shadowing_supervisor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    shadowing_rating: Mapped[Optional[float]] = mapped_column(Float)
    
    # Phase 5: Independent Supervised
    supervised_tasks_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Reviewer Info
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    supervisor = relationship("User", foreign_keys=[shadowing_supervisor_id])
