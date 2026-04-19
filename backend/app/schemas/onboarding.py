from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
import uuid

class ContractSignRequest(BaseModel):
    signee_name: str
    signature_data: str # Base64
    ip_address: Optional[str] = None

class QuizSubmission(BaseModel):
    module_id: uuid.UUID
    answers: Dict[str, str]

class ShadowingEvaluation(BaseModel):
    rubric: Dict[str, int]
    notes: Optional[str] = None
    recommendation: str # ready, retraining, rejected

class TrainingModuleResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    video_url: Optional[str] = None
    order: int
    quiz_questions_count: int

    class Config:
        from_attributes = True
