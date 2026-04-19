from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid

class VerificationReportCreate(BaseModel):
    assignment_id: uuid.UUID
    listing_id: uuid.UUID
    exists: bool = True
    verified_quantity: float
    matching_grade: str
    photos: List[str]
    latitude: float
    longitude: float
    geo_timestamp: datetime
    notes: Optional[str] = None
    is_approved: bool = True

class DeliveryReportCreate(BaseModel):
    assignment_id: uuid.UUID
    order_id: uuid.UUID
    delivered_quantity: float
    quality_confirmed: bool = True
    handover_photos: List[str]
    buyer_signature: Optional[str] = None
    farmer_signature: Optional[str] = None
    is_complete: bool = True
    discrepancy_notes: Optional[str] = None

class AgentTaskView(BaseModel):
    id: uuid.UUID
    assignment_type: str
    listing_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    dispute_id: Optional[uuid.UUID] = None
    status: str
    priority: int
    deadline: Optional[datetime] = None
    assigned_at: datetime
    bounty_amount: float

    class Config:
        from_attributes = True
