"""
Admin approval workflow endpoints.

Mounted at `/api/v1/admin/approvals`.
Accessible to ADMIN, REGIONAL_MANAGER, SUPER_ADMIN.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.security import (
    AdminApproval,
    ApprovalAction,
    ApprovalStatus,
)
from app.models.user import User, UserRole
from app.schemas.security import (
    ApprovalDecisionIn,
    ApprovalOut,
    ApprovalRequestIn,
)
from app.services import admin_approval_service

logger = logging.getLogger(__name__)
router = APIRouter()


_ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER)


@router.post("/request", response_model=ApprovalOut)
def request_approval(
    body: ApprovalRequestIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    try:
        action = ApprovalAction(body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown action '{body.action}'") from exc

    approval = admin_approval_service.request_approval(
        db,
        requested_by=actor,
        action=action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        amount=body.amount,
        currency=body.currency,
        reason=body.reason,
    )
    db.commit()
    db.refresh(approval)
    return approval


@router.get("", response_model=list[ApprovalOut])
def list_approvals(
    status_filter: Optional[ApprovalStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    q = db.query(AdminApproval)
    if status_filter:
        q = q.filter(AdminApproval.status == status_filter)
    return q.order_by(AdminApproval.requested_at.desc()).limit(limit).all()


@router.get("/{approval_id}", response_model=ApprovalOut)
def get_approval(
    approval_id: UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    approval = db.query(AdminApproval).filter(AdminApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
def approve(
    approval_id: UUID,
    body: ApprovalDecisionIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    approval = admin_approval_service.approve(db, approval_id=approval_id, actor=actor)
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
def reject(
    approval_id: UUID,
    body: ApprovalDecisionIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_ADMIN_ROLES)),
):
    if not body.reason:
        raise HTTPException(status_code=400, detail="Rejection reason required")
    approval = admin_approval_service.reject(
        db, approval_id=approval_id, actor=actor, reason=body.reason
    )
    db.commit()
    db.refresh(approval)
    return approval
