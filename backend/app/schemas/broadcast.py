import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.broadcast import BroadcastStatus, BroadcastAudience


class BroadcastCreate(BaseModel):
    subject: Optional[str] = None
    message: str
    audience: BroadcastAudience = BroadcastAudience.ALL
    audience_filter: Optional[dict] = None
    channels: List[str] # ["sms", "whatsapp", "email"]
    scheduled_for: Optional[datetime] = None


class BroadcastOut(BaseModel):
    id: uuid.UUID
    subject: Optional[str]
    message: str
    audience: BroadcastAudience
    channels: List[str]
    status: BroadcastStatus
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    sent_count: int
    delivered_count: int
    failed_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
