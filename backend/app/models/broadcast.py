import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, JSON, Integer, ForeignKey, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BroadcastStatus(str, enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BroadcastAudience(str, enum.Enum):
    ALL = "all"
    FARMERS = "farmers"
    BUYERS = "buyers"
    AGENTS = "agents"
    DRIVERS = "drivers"
    REGIONAL = "regional"


class BroadcastMessage(Base):
    """
    Broadcast messages sent to large groups of users via multiple channels.
    Part of the Admin Portal communication system.
    """
    __tablename__ = "broadcast_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[Optional[str]] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    audience: Mapped[BroadcastAudience] = mapped_column(Enum(BroadcastAudience), default=BroadcastAudience.ALL)
    audience_filter: Mapped[Optional[dict]] = mapped_column(JSON) # e.g. {"region": "Harare"}
    
    channels: Mapped[List[str]] = mapped_column(JSON) # e.g. ["sms", "whatsapp", "email"]
    
    status: Mapped[BroadcastStatus] = mapped_column(Enum(BroadcastStatus), default=BroadcastStatus.PENDING)
    
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Stats
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_by: Mapped[int] = mapped_column(ForeignKey("admin_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    author = relationship("AdminUser")
