import enum
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base

class ModuleStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class CertificationLevel(str, enum.Enum):
    TRAINEE = "trainee"
    CERTIFIED = "certified"
    SENIOR = "senior"
    MASTER = "master"

class AgentTraining(Base):
    __tablename__ = "agent_training"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False, unique=True)
    
    # Progress tracking
    module_1_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_2_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_3_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_4_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_5_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_6_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_7_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_8_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_9_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    module_10_status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.NOT_STARTED)
    
    # Quiz scores
    module_1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_2_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_3_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_4_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_5_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_6_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_7_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_8_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_9_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    module_10_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Exams
    mid_exam_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mid_exam_attempts: Mapped[int] = mapped_column(Integer, default=0)
    final_exam_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_exam_attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Field training
    shadowing_tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    supervised_tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    field_evaluation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Certification
    certification_level: Mapped[CertificationLevel] = mapped_column(SQLEnum(CertificationLevel), default=CertificationLevel.TRAINEE)
    certified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    certification_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Topic level tracking (JSON dictionary of {topic_id: bool})
    topics_progress: Mapped[Dict] = mapped_column(JSON, default=dict)
    
    # Exam Timing & Randomization
    last_exam_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    active_exam_question_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    agent = relationship("Agent")


class AcademyModule(Base):
    __tablename__ = "academy_modules" # Renamed from training_modules to avoid conflict
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    content_url: Mapped[Optional[str]] = mapped_column(String(500))  # Video/PDF URL
    topics: Mapped[Optional[List[Dict]]] = mapped_column(JSON) # List of topic metadata
    quiz_questions: Mapped[Optional[Dict]] = mapped_column(JSON)  # List of questions
    passing_score: Mapped[float] = mapped_column(Float, default=80.0)
    duration_hours: Mapped[float] = mapped_column(Float, default=2.0)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)



class ExamAttempt(Base):
    __tablename__ = "academy_exam_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(50))  # "mid" or "final"
    score: Mapped[float] = mapped_column(Float)
    answers: Mapped[Optional[Dict]] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    attempted_at = mapped_column(DateTime(timezone=True), server_default=func.now())
