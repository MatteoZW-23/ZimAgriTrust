from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime
import uuid

class ModuleProgressUpdate(BaseModel):
    quiz_score: float

class ExamSubmission(BaseModel):
    correct_answers: Optional[int] = 0
    answers: Dict

class CertificationRequest(BaseModel):
    agent_id: uuid.UUID

class AcademyModuleBase(BaseModel):
    number: int
    title: str
    description: Optional[str] = None
    status: str
    score: Optional[float] = None

class AcademyProgressResponse(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    certification_level: str
    overall_progress: float
    modules_completed: int
    modules: List[dict]
    mid_exam: dict
    final_exam: dict
    field_training: dict

class TraineeLogin(BaseModel):
    agent_code: str
    pin: str

class TraineeToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent_code: str

    model_config = ConfigDict(from_attributes=True)
