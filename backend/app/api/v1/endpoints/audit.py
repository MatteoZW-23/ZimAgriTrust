from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity: str
    status: str
    timestamp: str
