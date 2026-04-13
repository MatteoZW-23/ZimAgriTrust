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
    
    model_config = ConfigDict(from_attributes=True)
