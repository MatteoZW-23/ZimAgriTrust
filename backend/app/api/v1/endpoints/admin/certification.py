from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, require_roles
from app.models.user import UserRole
from app.services.certification_service import certification_service

router = APIRouter()


@router.post("/check-expiry")
def check_certification_expiry(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN))
):
    """Admin endpoint to check all certifications for expiry and send notifications"""
    return certification_service.check_certification_expiry(db)


@router.post("/{agent_id}/renew")
def renew_agent_certification(
    agent_id: str,
    renewal_days: Optional[int] = 365,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN))
):
    """Admin endpoint to renew an agent's certification"""
    try:
        return certification_service.renew_certification(db, agent_id, renewal_days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
