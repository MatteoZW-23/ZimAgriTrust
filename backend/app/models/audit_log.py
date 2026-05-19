import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, JSON, Integer, ForeignKey, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """
    Tamper-proof, immutable audit trail for ZimAgriTrust.
    Each entry is cryptographically linked to the previous one using SHA-256 checksums.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Actors
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admin_users.id"), index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Action details
    action: Mapped[str] = mapped_column(String(100), index=True) # e.g. CREATE_LISTING, REJECT_AGENT
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), index=True) # e.g. TRANSACTION, USER
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Data changes
    old_values: Mapped[Optional[dict]] = mapped_column(JSON)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON)
    details: Mapped[Optional[dict]] = mapped_column(JSON) # Additional context
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Result status
    status: Mapped[str] = mapped_column(String(20), default="success") # success, failure, warning
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tamper-proofing
    # SHA-256(previous_log.checksum + current_log_payload)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    admin = relationship("AdminUser")
    user = relationship("User")
