import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Enum, Float, Integer, String, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class VerificationStatus(str, enum.Enum):
    PENDING_AGENT = "pending_agent"
    PENDING_ADMIN = "pending_admin"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    RESUBMISSION_REQUESTED = "resubmission_requested"

class DocumentType(str, enum.Enum):
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    PROOF_OF_ADDRESS = "proof_of_address"
    FARM_REGISTRATION = "farm_registration"
    BUSINESS_REGISTRATION = "business_registration"
    TAX_CLEARANCE = "tax_clearance"
    AGENT_APPLICATION = "agent_application"
    VEHICLE_REGISTRATION = "vehicle_registration"

class ReviewerRole(str, enum.Enum):
    AGENT = "agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class DocumentVerificationRecord(Base):
    __tablename__ = "document_verification_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    document_label: Mapped[str] = mapped_column(String(100))
    status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.PENDING_ADMIN)
    
    # Review workflow
    current_stage: Mapped[str] = mapped_column(String(50), default="admin_review")
    required_reviewer_role: Mapped[ReviewerRole] = mapped_column(Enum(ReviewerRole), default=ReviewerRole.ADMIN)
    
    # File storage
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    back_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    selfie_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    supporting_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Document info
    document_number: Mapped[Optional[str]] = mapped_column(String(100))
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(100))
    issue_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Fraud & Auto-screening
    fraud_score: Mapped[float] = mapped_column(Float, default=0)
    fraud_flags: Mapped[list] = mapped_column(JSON, default=list)
    duplicate_check_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_screen_score: Mapped[float] = mapped_column(Float, default=0)
    auto_screen_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Reviewers
    agent_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    agent_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    agent_decision: Mapped[Optional[str]] = mapped_column(String(20))
    agent_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    admin_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    admin_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    admin_decision: Mapped[Optional[str]] = mapped_column(String(20))
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Resubmission
    resubmission_count: Mapped[int] = mapped_column(Integer, default=0)
    max_resubmissions: Mapped[int] = mapped_column(Integer, default=3)
    resubmission_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    rejection_category: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Trust Score
    trust_score_delta: Mapped[int] = mapped_column(Integer, default=0)
    trust_score_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserVerificationSummary(Base):
    __tablename__ = "user_verification_summaries"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    overall_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.PENDING_ADMIN)
    verification_level: Mapped[int] = mapped_column(Integer, default=0)
    
    identity_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.PENDING_ADMIN)
    identity_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    identity_document_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Permissions based on verification
    can_list_products: Mapped[bool] = mapped_column(Boolean, default=False)
    can_make_purchases: Mapped[bool] = mapped_column(Boolean, default=False)
    can_receive_payments: Mapped[bool] = mapped_column(Boolean, default=False)
    can_access_loans: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_platform_services: Mapped[bool] = mapped_column(Boolean, default=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VerificationQueue(Base):
    __tablename__ = "verification_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_verification_records.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    priority_score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, assigned, completed
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VerificationAuditLog(Base):
    __tablename__ = "verification_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_verification_records.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    actor_role: Mapped[str] = mapped_column(String(20))
    
    previous_status: Mapped[Optional[str]] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
