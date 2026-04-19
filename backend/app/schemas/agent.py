import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models.agent import AgentSpecialization, AgentStatus

class AgentCreate(BaseModel):
    user_id: uuid.UUID
    agent_code: str
    specialization: AgentSpecialization = AgentSpecialization.ALL

class AgentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    agent_code: str
    specialization: AgentSpecialization
    status: AgentStatus
    rating: float
    total_verifications: int
    
    model_config = ConfigDict(from_attributes=True)

class AgentAssignmentResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    assignment_type: str
    listing_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    dispute_id: Optional[uuid.UUID] = None
    status: str
    assigned_at: datetime
    deadline: Optional[datetime] = None
    bounty_amount: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)

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
