from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.services.ai_assistant_service import ai_assistant_service


router = APIRouter()


ADMIN_ROLES = {
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
    UserRole.REGIONAL_ADMIN,
    UserRole.REGIONAL_MANAGER,
    UserRole.FINANCE_ADMIN,
    UserRole.SYSTEM_ADMIN,
}


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    context: Optional[Dict[str, Any]] = None


class RecommendationRequest(BaseModel):
    assistant_role: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class MarketIntelligenceRequest(BaseModel):
    product: Optional[str] = None
    crop: Optional[str] = None
    sector: Optional[str] = None
    province: Optional[str] = None


class PredictionRequest(BaseModel):
    product: Optional[str] = Field(default=None, min_length=2, max_length=80)
    crop: Optional[str] = Field(default=None, min_length=2, max_length=80)
    sector: Optional[str] = Field(default=None, min_length=2, max_length=80)
    province: Optional[str] = None
    days_ahead: int = Field(default=30, ge=1, le=90)


def _authorize_assistant(assistant_role: str, user: User) -> str:
    try:
        role = ai_assistant_service.normalize_assistant_role(assistant_role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if role == "admin" and user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin AI is restricted to admin users.")
    if role == "agent" and user.role not in ADMIN_ROLES | {UserRole.AGENT}:
        raise HTTPException(status_code=403, detail="Agent AI is restricted to agents and admins.")
    return role


@router.post("/assistants/{assistant_role}/chat")
def chat_with_assistant(
    assistant_role: str,
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Role-specific AI assistant endpoint for farmer, buyer, supplier, agent, and admin guidance."""
    role = _authorize_assistant(assistant_role, current_user)
    return ai_assistant_service.answer(
        db=db,
        current_user=current_user,
        assistant_role=role,
        message=payload.message,
        context=payload.context,
    )


@router.post("/recommendations")
def get_ai_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns AI-driven next-best actions for the current user or requested assistant role."""
    role = payload.assistant_role
    if role:
        role = _authorize_assistant(role, current_user)
    return ai_assistant_service.recommendations(db, current_user, role, payload.context)


@router.post("/market-intelligence")
def get_market_intelligence(
    payload: MarketIntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregates platform supply, demand, and pricing signals for all agriculture sectors."""
    product = payload.product or payload.crop or payload.sector
    return ai_assistant_service.market_intelligence(db, product=product, province=payload.province)


@router.post("/predictions/price-demand")
def predict_price_and_demand(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Predicts agriculture product price and demand using platform signals and existing benchmark pricing."""
    product = payload.product or payload.crop or payload.sector
    if not product:
        raise HTTPException(status_code=422, detail="product, crop, or sector is required.")
    return ai_assistant_service.price_and_demand_prediction(
        db=db,
        product=product,
        province=payload.province,
        days_ahead=payload.days_ahead,
    )


@router.get("/disputes/{dispute_id}/suggest-resolution")
def suggest_dispute_resolution(
    dispute_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provides an agent/admin-reviewable dispute settlement suggestion."""
    if current_user.role not in ADMIN_ROLES | {UserRole.AGENT}:
        raise HTTPException(status_code=403, detail="Dispute AI suggestions are restricted to agents and admins.")
    try:
        return ai_assistant_service.dispute_resolution_suggestion(db, dispute_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
