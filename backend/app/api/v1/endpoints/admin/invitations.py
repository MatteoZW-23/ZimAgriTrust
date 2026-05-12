"""
Admin Invitation Management — `/api/v1/admin/invitations`

Super-admins can:
  • POST   /admin/invitations              → create + dispatch invitation
  • GET    /admin/invitations              → list (filter by status/role)
  • GET    /admin/invitations/{id}         → detail
  • DELETE /admin/invitations/{id}/revoke  → revoke pending invitation

The public acceptance endpoint already lives at /api/v1/auth/invitation/accept.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.models.rbac import Invitation, InvitationStatus, Role
from app.models.user import User, UserRole
from app.services.invitation_service import InvitationService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InvitationCreate(BaseModel):
    email: EmailStr
    role_name: str = Field(..., description="One of SYSTEM_ADMIN, FINANCE_ADMIN, REGIONAL_ADMIN, SUPPORT_ADMIN, BRANCH_ADMIN, AGENT, STAFF")
    phone: Optional[str] = Field(None, description="Optional — enables SMS + WhatsApp delivery")
    region: Optional[str] = Field(None, description="Required for REGIONAL_ADMIN")
    branch_id: Optional[int] = Field(None, description="Required for BRANCH_ADMIN")
    expires_hours: int = Field(72, ge=1, le=168)


class InvitationOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_acceptance_link(token: str) -> str:
    base = getattr(settings, "ADMIN_DASHBOARD_URL", None) or "https://admin.zimagritrust.com"
    return f"{base.rstrip('/')}/accept-invitation?token={token}"


async def _dispatch_invitation_async(
    email: str,
    phone: Optional[str],
    role_name: str,
    accept_link: str,
    inviter_name: str,
):
    """Send invitation via email + SMS + WhatsApp (best-effort, all parallel)."""
    subject = f"You've been invited as {role_name} at ZimAgriTrust"
    email_body = (
        f"Hello,\n\n"
        f"{inviter_name} has invited you to join ZimAgriTrust as {role_name}.\n\n"
        f"Click the secure link below to set up your account (valid for 72 hours):\n"
        f"{accept_link}\n\n"
        f"You will be required to set a strong password and enable two-factor "
        f"authentication using an authenticator app (Google Authenticator, Authy, etc.).\n\n"
        f"If you did not expect this invitation, please ignore this message.\n\n"
        f"— ZimAgriTrust Security Team"
    )
    sms_msg = (
        f"ZimAgriTrust: You've been invited as {role_name}. "
        f"Activate your account: {accept_link} (expires in 72h)"
    )
    wa_msg = (
        f"👑 *ZimAgriTrust Admin Invitation*\n\n"
        f"{inviter_name} has invited you as *{role_name}*.\n\n"
        f"Activate your account here:\n{accept_link}\n\n"
        f"_Link expires in 72 hours. You will set a password and configure 2FA._"
    )

    try:
        await NotificationService._send_email(email, subject, email_body)
    except Exception as exc:
        logger.warning("Invitation email failed for %s: %s", email, exc)

    if phone:
        try:
            NotificationService._send_sms(phone, sms_msg)
        except Exception as exc:
            logger.warning("Invitation SMS failed for %s: %s", phone, exc)
        try:
            await NotificationService._send_whatsapp(phone, wa_msg)
        except Exception as exc:
            logger.warning("Invitation WhatsApp failed for %s: %s", phone, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", summary="Create + dispatch admin invitation (Super Admin only)")
async def create_invitation(
    payload: InvitationCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    # Validate role-specific requirements
    if payload.role_name == "REGIONAL_ADMIN" and not payload.region:
        raise HTTPException(status_code=400, detail="region is required for REGIONAL_ADMIN")
    if payload.role_name == "BRANCH_ADMIN" and not payload.branch_id:
        raise HTTPException(status_code=400, detail="branch_id is required for BRANCH_ADMIN")

    try:
        invitation, token = InvitationService.create_invitation(
            db=db,
            email=payload.email,
            role_name=payload.role_name,
            invited_by=actor,
            expires_hours=payload.expires_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Dispatch notifications in background (do not block response)
    accept_link = _build_acceptance_link(token)
    background.add_task(
        _dispatch_invitation_async,
        email=payload.email,
        phone=payload.phone,
        role_name=payload.role_name,
        accept_link=accept_link,
        inviter_name=actor.full_name or "A ZimAgriTrust Super Admin",
    )

    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "role": payload.role_name,
        "status": invitation.status.value,
        "expires_at": invitation.expires_at.isoformat(),
        "delivery_channels": {
            "email": True,
            "sms": bool(payload.phone),
            "whatsapp": bool(payload.phone),
        },
        # Include token only in the immediate response so the super-admin can
        # share the link manually if delivery fails. Never store/log it.
        "acceptance_link": accept_link,
    }


@router.get("", summary="List admin invitations")
def list_invitations(
    status_filter: Optional[InvitationStatus] = Query(None, alias="status"),
    role_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    q = db.query(Invitation).join(Role, Invitation.role_id == Role.id)
    if status_filter:
        q = q.filter(Invitation.status == status_filter)
    if role_name:
        q = q.filter(Role.name == role_name)
    rows = q.order_by(Invitation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(inv.id),
            "email": inv.email,
            "role": inv.role.name if inv.role else None,
            "status": inv.status.value,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            "used_at": inv.used_at.isoformat() if inv.used_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in rows
    ]


@router.get("/{invitation_id}", summary="Get invitation details")
def get_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    inv = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return {
        "id": str(inv.id),
        "email": inv.email,
        "role": inv.role.name if inv.role else None,
        "status": inv.status.value,
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        "used_at": inv.used_at.isoformat() if inv.used_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "created_by": str(inv.created_by) if inv.created_by else None,
    }


@router.delete("/{invitation_id}/revoke", summary="Revoke pending invitation")
def revoke_invitation(
    invitation_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    inv = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if inv.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot revoke invitation in status {inv.status.value}",
        )
    try:
        InvitationService.revoke_invitation(db, invitation_id, reason=f"Revoked by {actor.email}")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": str(invitation_id), "status": "REVOKED"}
