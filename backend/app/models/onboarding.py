import enum
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base


class OnboardingPhase(str, enum.Enum):
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    EQUIPMENT = "equipment"
    SHADOWING = "shadowing"
    INDEPENDENT = "independent"
    CERTIFIED = "certified"


class TrainingModule(Base):
    """Catalog of training content for agents"""
    __tablename__ = "training_modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    video_url: Mapped[Optional[str]] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer) # Sequence in the academy
    min_pass_score: Mapped[float] = mapped_column(Float, default=80.0)
    quiz_data: Mapped[Dict] = mapped_column(JSON) # List of questions/options/answers


class AgentTrainingProgress(Base):
    """Tracks individual agent interaction with modules"""
    __tablename__ = "agent_training_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_applications.id"))
    module_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_modules.id"))
    
    status: Mapped[str] = mapped_column(String(20), default="not_started") # started, completed
    video_progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    quiz_score: Mapped[Optional[float]] = mapped_column(Float)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AgentContract(Base):
    """Digital contracts with e-signature tracking"""
    __tablename__ = "agent_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_applications.id"), unique=True)
    
    contract_type: Mapped[str] = mapped_column(String(50), default="service_level_agreement")
    content_hash: Mapped[str] = mapped_column(String(64)) # Integrity check of the signed version
    
    # E-Signature Data
    signed_by_name: Mapped[str] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    signature_base64: Mapped[Optional[str]] = mapped_column(Text) # Drawing path or base64 image
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ShadowingLog(Base):
    """Evaluation logs from senior agents"""
    __tablename__ = "shadowing_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_applications.id"))
    supervisor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    tasks_observed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_led: Mapped[int] = mapped_column(Integer, default=0)
    
    # Rubric Scores (1-5)
    technical_accuracy: Mapped[int] = mapped_column(Integer)
    professionalism: Mapped[int] = mapped_column(Integer)
    communication: Mapped[int] = mapped_column(Integer)
    
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(String(50)) # ready, retraining, rejected
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
