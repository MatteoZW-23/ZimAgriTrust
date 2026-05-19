import enum
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base


class EnrollmentStatus(str, enum.Enum):
    NOT_ENROLLED = "not_enrolled"
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResourceType(str, enum.Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    IMAGE = "image"
    LINK = "link"
    QUIZ = "quiz"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"


class Course(Base):
    __tablename__ = "classroom_courses"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module_number: Mapped[int] = mapped_column(Integer, nullable=False)
    passing_score: Mapped[float] = mapped_column(Float, default=80.0)
    estimated_hours: Mapped[float] = mapped_column(Float, default=2.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    topics = relationship("CourseTopic", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="course", cascade="all, delete-orphan")


class CourseTopic(Base):
    __tablename__ = "classroom_course_topics"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_courses.id"), nullable=False)
    topic_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="topics")
    resources = relationship("Resource", back_populates="topic", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "classroom_resources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_courses.id"), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_course_topics.id"), nullable=True)
    resource_type: Mapped[ResourceType] = mapped_column(SQLEnum(ResourceType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Quiz-specific fields
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passing_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course")
    topic = relationship("CourseTopic", back_populates="resources")
    quiz_questions = relationship("QuizQuestion", back_populates="resource", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="resource", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "classroom_quiz_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_resources.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(SQLEnum(QuestionType), nullable=False)
    options: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=1)
    order_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="quiz_questions")
    essay_answers = relationship("EssayAnswer", back_populates="question", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "classroom_enrollments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_courses.id"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ENROLLED)
    enrolled_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="enrollments")
    topic_progress = relationship("TopicProgress", back_populates="enrollment", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="enrollment", cascade="all, delete-orphan")


class TopicProgress(Base):
    __tablename__ = "classroom_topic_progress"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_enrollments.id"), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_course_topics.id"), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="topic_progress")


class QuizAttempt(Base):
    __tablename__ = "classroom_quiz_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_enrollments.id"), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_resources.id"), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    answers: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    started_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="quiz_attempts")
    resource = relationship("Resource", back_populates="quiz_attempts")
    essay_answers = relationship("EssayAnswer", back_populates="quiz_attempt", cascade="all, delete-orphan")


class EssayAnswer(Base):
    __tablename__ = "classroom_essay_answers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_quiz_attempts.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_quiz_questions.id"), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graded_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    graded_at = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quiz_attempt = relationship("QuizAttempt", back_populates="essay_answers")
    question = relationship("QuizQuestion", back_populates="essay_answers")


class Announcement(Base):
    __tablename__ = "classroom_announcements"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classroom_courses.id"), nullable=False)
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="announcements")
