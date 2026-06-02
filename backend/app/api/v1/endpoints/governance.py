from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.governance import ConsentType, PrivacyRequestType, PolicyScope, PolicyStatus
from app.models.user import User, UserRole
from app.services.governance_service import governance_service

router = APIRouter()


class ConsentPayload(BaseModel):
    consent_type: ConsentType
    policy_version: str
    accepted: bool = True
    acceptance_method: Optional[str] = "portal"


class CommPrefsPayload(BaseModel):
    whatsapp_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    marketing_enabled: Optional[bool] = None


class PrivacyRequestPayload(BaseModel):
    request_type: PrivacyRequestType
    reason: Optional[str] = None


class PolicyPayload(BaseModel):
    key: str
    category: str
    scope: PolicyScope = PolicyScope.LEGAL
    version: str
    title: str
    content: dict
    status: PolicyStatus = PolicyStatus.DRAFT
    requires_reacceptance: bool = True


class EnforcementPayload(BaseModel):
    requirement_key: str


@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    return governance_service.get_policies(db)

@router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Backward-compatible governance rules endpoint.
    """
    return governance_service.get_policies(db)


@router.post("/consents")
def record_consent(
    payload: ConsentPayload,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.upsert_consent(
        db=db,
        user=user,
        consent_type=payload.consent_type,
        policy_version=payload.policy_version,
        accepted=payload.accepted,
        ip_address=request.client.host if request.client else None,
        device=request.headers.get("User-Agent"),
        method=payload.acceptance_method,
        platform=request.headers.get("X-Platform", "api"),
    )


@router.get("/consents")
def my_consents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.get_consents(db, user)


@router.get("/preferences")
def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.get_or_create_preferences(db, user)


@router.put("/preferences")
def update_preferences(
    payload: CommPrefsPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.update_preferences(db, user, payload.model_dump(exclude_none=True))


@router.post("/privacy-requests")
def submit_privacy_request(
    payload: PrivacyRequestPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return governance_service.submit_privacy_request(db, user, payload.request_type, payload.reason)


@router.post("/admin/policies")
def upsert_policy(
    payload: PolicyPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ACADEMY_ADMIN)),
):
    return governance_service.create_or_update_policy(db, user, payload.model_dump())


@router.post("/admin/policies/{key}/publish")
def publish_policy(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return governance_service.publish_policy(db, user, key)


@router.post("/enforcement/check")
def check_enforcement(
    payload: EnforcementPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    governance_service.enforce_requirements(db, user, payload.requirement_key)
    return {"allowed": True}
