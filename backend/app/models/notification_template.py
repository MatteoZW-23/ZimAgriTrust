import enum
from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TemplateChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    APP = "app"


class NotificationTemplate(Base):
    """
    Module 10: Notification Management
    Dynamic templates for automated outreach.
    """
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False) # e.g., NEW_OFFER, DISPUTE_OPEN
    channel: Mapped[TemplateChannel] = mapped_column(default=TemplateChannel.WHATSAPP)
    content: Mapped[str] = mapped_column(Text, nullable=False) # Supporting double curlies like {{user_name}}
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at = mapped_column(String(30), nullable=True) # Placeholder for simple stamp
