from datetime import datetime, timedelta
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

@router.get("/security-logs", response_model=List[AuditLogResponse])
def get_security_audit_logs(
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Simulates fetching system-wide audit logs.
    In a production app, this would query a dedicated AuditLog table.
    """
    # Mock some dynamic timestamps
    now = datetime.utcnow()
    return [
        {
            "id": 1,
            "action": "USER_VERIFY",
            "entity": "Farmer #2638841",
            "status": "SUCCESS",
            "timestamp": (now - timedelta(minutes=5)).strftime("%H:%M:%S") + " UTC",
        },
        {
            "id": 2,
            "action": "ESCROW_RELEASE",
            "entity": "Tx 1422 (Maize)",
            "status": "SUCCESS",
            "timestamp": (now - timedelta(minutes=14)).strftime("%H:%M:%S") + " UTC",
        },
        {
            "id": 3,
            "action": "DISPUTE_OPEN",
            "entity": "Tx 1500 (Beans)",
            "status": "SYSTEM_FLAG",
            "timestamp": (now - timedelta(hours=1)).strftime("%H:%M:%S") + " UTC",
        },
        {
            "id": 4,
            "action": "SECURITY_SCAN",
            "entity": "Network Hub",
            "status": "CLEAN",
            "timestamp": (now - timedelta(hours=3)).strftime("%H:%M:%S") + " UTC",
        },
    ]
