import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.api.deps import get_db
from sqlalchemy.orm import Session
from app.services.agent_onboarding_service import agent_onboarding_service
from app.schemas.recruitment import AgentApplicationCreate

router = APIRouter()

@router.get("/my-status/{user_id}")
async def get_agent_status(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns current position in the 10-step recruitment pipeline - uses unified onboarding service.
    """
    return agent_onboarding_service.get_application_status(db, user_id)


@router.post("/application/resubmit")
async def resubmit_application(
    payload: AgentApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Resubmit a rejected agent application with updated details.
    Marks any prior REJECTED record as superseded and creates a fresh APPLIED row.
    """
    from app.models.recruitment import AgentApplication, ApplicationStatus

    prior = (
        db.query(AgentApplication)
        .filter(AgentApplication.national_id == payload.national_id)
        .order_by(AgentApplication.created_at.desc())
        .first()
        if hasattr(AgentApplication, "created_at")
        else db.query(AgentApplication)
        .filter(AgentApplication.national_id == payload.national_id)
        .first()
    )

    if prior and prior.status not in {ApplicationStatus.REJECTED}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resubmit while existing application is in status {prior.status}",
        )

    # Mark prior rejected record as archived by clearing its national_id so the
    # uniqueness check in submit_application succeeds.
    if prior:
        prior.national_id = f"{prior.national_id}::ARCHIVED::{prior.id}"
        db.commit()

    return await agent_onboarding_service.submit_application(db, payload)

@router.get("/{agent_code}/verify")
def verify_agent_public(agent_code: str, db: Session = Depends(get_db)):
    """
    Publicly verify an agent by their code. Used by farmers to scan QR codes on certificates.
    """
    from app.models.agent import Agent, AgentStatus
    from app.models.academy import AgentTraining, CertificationLevel
    
    agent = db.query(Agent).filter(Agent.agent_code == agent_code).first()
    if not agent:
        return {
            "is_valid": False,
            "message": "❌ Invalid Agent Code. This person is not a recognized ZimAgritrust representative."
        }
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == agent.id).first()
    
    status_msg = "ACTIVE" if agent.status == AgentStatus.ACTIVE else agent.status.value.upper()
    is_certified = training and training.certification_level == CertificationLevel.CERTIFIED
    
    return {
        "is_valid": True,
        "full_name": agent.user.full_name,
        "status": status_msg,
        "is_certified": is_certified,
        "certified_since": training.certified_at if training else None,
        "expires_at": training.certification_expires_at if training else None,
        "region": f"{agent.province}, {agent.district}",
        "specialization": agent.specialization,
        "message": "✅ Official ZimAgritrust Agent Verified." if is_certified else "⚠️ Trainee Agent / Pending Certification."
    }

