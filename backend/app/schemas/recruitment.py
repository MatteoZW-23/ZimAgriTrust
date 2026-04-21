from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime
from app.models.recruitment import ApplicationStatus

class AgentApplicationCreate(BaseModel):
    full_name: str
    phone_number: str
    national_id: str
    province: str
    district: str
    has_smartphone: bool
    has_transport: bool
    transport_type: Optional[str] = None
    agri_experience_years: int
    specializations: List[str]

class AgentApplicationResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    province: str
    status: ApplicationStatus
    training_modules_completed: List[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TrainingUpdate(BaseModel):
    progress_delta: float
    module_name: str

class TestResult(BaseModel):
    score: float
    passed: bool
