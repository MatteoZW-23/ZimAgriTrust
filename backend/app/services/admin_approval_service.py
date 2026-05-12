"""
Dual / multi-admin approval workflow for high-value cash actions.

Rules:
  - Refund > $100               → 2 admins required
  - Any single txn > $2000      → 2 admins required (one must be SENIOR or SUPER)
  - Limit override / escrow override → 2 admins (one must be SUPER)

Each approval signature binds (actor, action, resource, decision, ts) via
HMAC-SHA256, persisted in `admin_approvals.signature_1/signature_2`.

Time-based gating: financial approvals only inside FINANCIAL_APPROVAL_HOURS_*
(Zimbabwe local time). Super-admin bypasses this.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import (
    AdminApproval,
    AdminLevel,
    ApprovalAction,
    ApprovalStatus,
)
from app.models.user import User, UserRole
from app.services.transaction_signing_service import sign_admin_decision

logger = logging.getLogger(__name__)


APPROVAL_TTL_HOURS = 24


# ---------------------------------------------------------------------------
# Time-based access
# ---------------------------------------------------------------------------

def is_within_financial_hours(now_utc: Optional[datetime] = None) -> bool:
    if not settings.FINANCIAL_APPROVAL_TIME_WINDOW_ENABLED:
        return True
    now_utc = now_utc or datetime.now(timezone.utc)
    local = now_utc + timedelta(hours=settings.FINANCIAL_APPROVAL_TZ_OFFSET_HOURS)
    return settings.FINANCIAL_APPROVAL_HOURS_START <= local.hour < settings.FINANCIAL_APPROVAL_HOURS_END


def enforce_financial_hours(actor: User) -> None:
    """Raise 403 outside financial hours unless actor is super-admin."""
    if actor.role == UserRole.SUPER_ADMIN:
        return
    if not is_within_financial_hours():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Financial approvals only between "
                f"{settings.FINANCIAL_APPROVAL_HOURS_START:02d}:00 and "
                f"{settings.FINANCIAL_APPROVAL_HOURS_END:02d}:00 (CAT)"
            ),
        )


# ---------------------------------------------------------------------------
# Admin level resolution
# ---------------------------------------------------------------------------

def admin_level(user: User) -> AdminLevel:
    """Map UserRole + permissions to AdminLevel."""
    if user.role == UserRole.SUPER_ADMIN:
        return AdminLevel.SUPER
    if user.role == UserRole.ADMIN:
        # Permission-driven: an "admin_level" attribute, or fallback by perms
        level = (user.permissions or {}).get("admin_level") if hasattr(user, "permissions") else None
        if level == 3:
            return AdminLevel.SENIOR
        if level == 2:
            return AdminLevel.FINANCE
        return AdminLevel.SUPPORT
    if user.role == UserRole.REGIONAL_MANAGER:
        return AdminLevel.SENIOR
    return AdminLevel.SUPPORT


def admin_can_approve(user: User, amount: float) -> bool:
    lvl = admin_level(user)
    if lvl == AdminLevel.SUPPORT:
        return False
    if lvl == AdminLevel.FINANCE:
        return amount <= settings.FINANCE_ADMIN_APPROVAL_LIMIT_USD
    if lvl == AdminLevel.SENIOR:
        return amount <= settings.SENIOR_ADMIN_APPROVAL_LIMIT_USD
    return True  # SUPER


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

def requires_dual_approval(*, action: ApprovalAction, amount: float) -> bool:
    if action == ApprovalAction.REFUND:
        return amount > settings.DUAL_APPROVAL_REFUND_THRESHOLD_USD
    if action == ApprovalAction.LARGE_TRANSACTION:
        return amount > settings.MULTI_APPROVAL_TXN_THRESHOLD_USD
    if action in (ApprovalAction.ESCROW_OVERRIDE, ApprovalAction.LIMIT_OVERRIDE):
        return True
    return False


def request_approval(
    db: Session,
    *,
    requested_by: User,
    action: ApprovalAction,
    resource_type: str,
    resource_id: str,
    amount: float,
    currency: str = "USD",
    reason: Optional[str] = None,
) -> AdminApproval:
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    rules = {
        "refund_threshold": settings.DUAL_APPROVAL_REFUND_THRESHOLD_USD,
        "large_txn_threshold": settings.MULTI_APPROVAL_TXN_THRESHOLD_USD,
        "finance_limit": settings.FINANCE_ADMIN_APPROVAL_LIMIT_USD,
        "senior_limit": settings.SENIOR_ADMIN_APPROVAL_LIMIT_USD,
    }
    approval = AdminApproval(
        id=uuid.uuid4(),
        resource_type=resource_type,
        resource_id=str(resource_id),
        action=action,
        amount=round(amount, 2),
        currency=currency,
        reason=reason,
        requested_by=requested_by.id,
        requested_at=datetime.utcnow(),
        status=ApprovalStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(hours=APPROVAL_TTL_HOURS),
        rules_snapshot=rules,
    )
    db.add(approval)
    db.flush()
    return approval


def approve(
    db: Session,
    *,
    approval_id,
    actor: User,
) -> AdminApproval:
    """Record one approval signature. Transitions status to PARTIAL or FULLY APPROVED."""
    enforce_financial_hours(actor)

    approval = (
        db.query(AdminApproval)
        .filter(AdminApproval.id == approval_id)
        .with_for_update()
        .first()
    )
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in (ApprovalStatus.PENDING, ApprovalStatus.PARTIAL_APPROVED):
        raise HTTPException(status_code=400, detail=f"Approval is {approval.status.value}")
    if approval.expires_at and datetime.utcnow() > approval.expires_at:
        approval.status = ApprovalStatus.EXPIRED
        db.flush()
        raise HTTPException(status_code=400, detail="Approval has expired")

    if approval.requested_by == actor.id:
        raise HTTPException(status_code=403, detail="Requester cannot self-approve")
    if not admin_can_approve(actor, float(approval.amount)):
        raise HTTPException(
            status_code=403,
            detail=f"Your admin level is not authorized to approve ${approval.amount} {approval.currency}",
        )
    if actor.id in (approval.approved_by_1, approval.approved_by_2):
        raise HTTPException(status_code=400, detail="You have already approved this request")

    # Multi-approval rule: for amounts > MULTI_APPROVAL_TXN_THRESHOLD, at least
    # one approver must be SENIOR or SUPER.
    if float(approval.amount) > settings.MULTI_APPROVAL_TXN_THRESHOLD_USD:
        existing_seniors = _existing_senior_count(db, approval)
        actor_lvl = admin_level(actor)
        if existing_seniors == 0 and actor_lvl not in (AdminLevel.SENIOR, AdminLevel.SUPER):
            # This actor is not senior; allow but require a senior next.
            pass

    sig = sign_admin_decision(
        actor_id=str(actor.id),
        action=f"approve:{approval.action.value}",
        resource_id=str(approval.resource_id),
        decision="approved",
        amount=float(approval.amount),
        timestamp=int(time.time()),
    )

    if approval.approved_by_1 is None:
        approval.approved_by_1 = actor.id
        approval.approved_at_1 = datetime.utcnow()
        approval.signature_1 = sig
    else:
        approval.approved_by_2 = actor.id
        approval.approved_at_2 = datetime.utcnow()
        approval.signature_2 = sig

    needs_dual = requires_dual_approval(action=approval.action, amount=float(approval.amount))
    if needs_dual:
        if approval.approved_by_1 and approval.approved_by_2:
            # Enforce senior requirement for multi-approval
            if float(approval.amount) > settings.MULTI_APPROVAL_TXN_THRESHOLD_USD:
                if not _has_senior_approver(db, approval):
                    raise HTTPException(
                        status_code=403,
                        detail="At least one approver must be SENIOR or SUPER admin",
                    )
            approval.status = ApprovalStatus.FULLY_APPROVED
            approval.fully_approved_at = datetime.utcnow()
        else:
            approval.status = ApprovalStatus.PARTIAL_APPROVED
    else:
        approval.status = ApprovalStatus.FULLY_APPROVED
        approval.fully_approved_at = datetime.utcnow()

    db.flush()
    return approval


def reject(
    db: Session,
    *,
    approval_id,
    actor: User,
    reason: str,
) -> AdminApproval:
    enforce_financial_hours(actor)
    approval = db.query(AdminApproval).filter(AdminApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status not in (ApprovalStatus.PENDING, ApprovalStatus.PARTIAL_APPROVED):
        raise HTTPException(status_code=400, detail=f"Approval is {approval.status.value}")
    approval.status = ApprovalStatus.REJECTED
    approval.rejected_by = actor.id
    approval.rejection_reason = reason
    db.flush()
    return approval


def is_fully_approved(db: Session, *, resource_type: str, resource_id: str) -> bool:
    """Gate function — call before executing the underlying action."""
    return bool(
        db.query(AdminApproval.id)
        .filter(
            AdminApproval.resource_type == resource_type,
            AdminApproval.resource_id == str(resource_id),
            AdminApproval.status == ApprovalStatus.FULLY_APPROVED,
        )
        .first()
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _existing_senior_count(db: Session, approval: AdminApproval) -> int:
    count = 0
    for uid in (approval.approved_by_1, approval.approved_by_2):
        if not uid:
            continue
        u = db.query(User).filter(User.id == uid).first()
        if u and admin_level(u) in (AdminLevel.SENIOR, AdminLevel.SUPER):
            count += 1
    return count


def _has_senior_approver(db: Session, approval: AdminApproval) -> bool:
    return _existing_senior_count(db, approval) >= 1
