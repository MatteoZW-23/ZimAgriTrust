"""
Super-admin endpoints — mounted under `/api/v1/super-admin`.

ALL endpoints (except login/verify-mfa) require a super-admin bearer token
issued by `verify_mfa`. The token has its own signing key and a 30-min expiry.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_super_admin import get_current_super_admin
from app.core.config import settings
from app.models.security import (
    AdminActionLog,
    FraudAlert,
    FraudSeverity,
    SuperAdmin,
    UserTier,
    WithdrawalLimit,
)
from app.schemas.security import (
    AuditChainStatus,
    EmergencyShutdownIn,
    FraudAlertOut,
    FraudAlertResolveIn,
    SuperAdminLoginRequest,
    SuperAdminMfaVerifyRequest,
    SuperAdminPreMfaResponse,
    SuperAdminTokenResponse,
    WithdrawalLimitOut,
    WithdrawalLimitUpdateIn,
)
from app.schemas.security import (
    EscrowReleaseConfirmIn,
    EscrowReleaseRequestIn,
)
from app.services import super_admin_service
from app.services.audit_chain_service import verify_chain, verify_record
from app.services.fraud_detection_service import list_open_alerts, resolve_alert
from app.services.reconciliation_service import run_daily_reconciliation
from app.services.transaction_signing_service import sign_admin_decision

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.options("/login")
async def super_admin_login_options(request: Request):
    """Handle CORS preflight for login"""
    return {"status": "ok"}


@router.post("/login", response_model=SuperAdminPreMfaResponse)
def super_admin_login(
    body: SuperAdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return super_admin_service.login_step_1(
        db, request=request, username=body.username, password=body.password
    )


@router.post("/verify-mfa", response_model=SuperAdminTokenResponse)
def super_admin_verify_mfa(
    body: SuperAdminMfaVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return super_admin_service.verify_mfa(
        db,
        request=request,
        pre_mfa_token=body.pre_mfa_token,
        mfa_code=body.mfa_code,
        method=body.method,
    )


@router.get("/me")
def super_admin_me(current: SuperAdmin = Depends(get_current_super_admin)):
    return {
        "id": current.id,
        "username": current.username,
        "email": current.email,
        "last_login_at": current.last_login_at,
        "last_login_ip": current.last_login_ip,
    }


# ---------------------------------------------------------------------------
# Fraud alerts
# ---------------------------------------------------------------------------

@router.get("/fraud-alerts", response_model=list[FraudAlertOut])
def list_fraud_alerts(
    severity: Optional[FraudSeverity] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    return list_open_alerts(db, severity=severity, limit=limit)


@router.post("/fraud-alerts/{alert_id}/resolve", response_model=FraudAlertOut)
def resolve_fraud_alert(
    alert_id: str,
    body: FraudAlertResolveIn,
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    try:
        alert = resolve_alert(db, alert_id=alert_id, super_admin_id=current.id, notes=body.notes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    _log_action(db, current, "resolve_fraud_alert", "fraud_alert", str(alert.id))
    return alert


# ---------------------------------------------------------------------------
# Audit chain verification
# ---------------------------------------------------------------------------

@router.get("/audit/verify-chain", response_model=AuditChainStatus)
def audit_verify_chain(
    limit: int = Query(5000, ge=100, le=100000),
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    return verify_chain(db, limit=limit)


@router.get("/audit/verify-record")
def audit_verify_record(
    table_name: str = Query(...),
    record_id: str = Query(...),
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    return verify_record(db, table_name, record_id)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

@router.get("/reconciliation/daily")
def reconciliation_daily(
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    report = run_daily_reconciliation(db)
    _log_action(db, current, "reconciliation_daily", payload=report)
    db.commit()
    return report


# ---------------------------------------------------------------------------
# Withdrawal limits
# ---------------------------------------------------------------------------

@router.get("/limits", response_model=list[WithdrawalLimitOut])
def list_limits(
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    return db.query(WithdrawalLimit).all()


@router.post("/limits/{tier}", response_model=WithdrawalLimitOut)
def update_limit(
    tier: UserTier,
    body: WithdrawalLimitUpdateIn,
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    row = db.query(WithdrawalLimit).filter(WithdrawalLimit.user_tier == tier).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tier not found")
    row.daily_limit = body.daily_limit
    row.weekly_limit = body.weekly_limit
    row.monthly_limit = body.monthly_limit
    row.per_transaction_limit = body.per_transaction_limit
    if body.min_trust_score is not None:
        row.min_trust_score = body.min_trust_score
    row.updated_by = current.id
    db.commit()
    db.refresh(row)
    _log_action(
        db, current, "update_limit", "withdrawal_limit", tier.value, payload=body.model_dump()
    )
    db.commit()
    return row


# ---------------------------------------------------------------------------
# Emergency shutdown
# ---------------------------------------------------------------------------

@router.post("/system/shutdown")
def emergency_shutdown(
    body: EmergencyShutdownIn,
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to execute shutdown")
    from app.models.system_config import SystemConfig
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "SYSTEM_LOCKDOWN").first()
    if cfg:
        cfg.value = "true"
    else:
        db.add(SystemConfig(key="SYSTEM_LOCKDOWN", value="true"))
    db.commit()
    _log_action(db, current, "emergency_shutdown", payload={"reason": body.reason})
    db.commit()
    logger.critical("EMERGENCY SHUTDOWN by super-admin %s: %s", current.username, body.reason)
    return {"status": "shutdown_engaged", "reason": body.reason}


@router.post("/escrow/request-release")
async def escrow_request_release(
    body: EscrowReleaseRequestIn,
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    """Step 1 of two-key release: generate platform signature + send admin OTP."""
    from app.services.escrow_two_key_service import request_release
    # Build a synthetic User-like actor for the audit trail / SMS routing.
    # The escrow service uses the User model for phone routing; for super-admin
    # we instead use SUPER_ADMIN_ALERT_PHONE as the OTP destination.
    from types import SimpleNamespace
    from app.models.user import UserRole as _UR
    actor = SimpleNamespace(
        id=current.id,
        role=_UR.SUPER_ADMIN,
        phone_number=current.phone_number or settings.SUPER_ADMIN_ALERT_PHONE,
    )
    result = await request_release(db, order_id=body.order_id, admin=actor)
    _log_action(db, current, "escrow_request_release", "order", str(body.order_id))
    db.commit()
    return result


@router.post("/escrow/confirm-release")
async def escrow_confirm_release(
    body: EscrowReleaseConfirmIn,
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    """Step 2: validate OTP + signature, execute release."""
    from app.services.escrow_two_key_service import confirm_release
    from types import SimpleNamespace
    from app.models.user import UserRole as _UR
    actor = SimpleNamespace(
        id=current.id,
        role=_UR.SUPER_ADMIN,
        phone_number=current.phone_number or settings.SUPER_ADMIN_ALERT_PHONE,
    )
    order = await confirm_release(
        db,
        order_id=body.order_id,
        admin=actor,
        otp=body.otp,
        handover_code=body.handover_code,
    )
    _log_action(
        db, current, "escrow_confirm_release", "order", str(order.id),
        amount=float(order.total_amount),
    )
    db.commit()
    return {
        "order_id": str(order.id),
        "status": order.status.value,
        "amount": float(order.total_amount),
        "currency": order.currency,
    }


@router.post("/system/resume")
def resume_platform(
    db: Session = Depends(get_db),
    current: SuperAdmin = Depends(get_current_super_admin),
):
    from app.models.system_config import SystemConfig
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "SYSTEM_LOCKDOWN").first()
    if cfg:
        cfg.value = "false"
    db.commit()
    _log_action(db, current, "resume_platform")
    db.commit()
    return {"status": "platform_resumed"}


# ---------------------------------------------------------------------------
# Admin action log helper
# ---------------------------------------------------------------------------

def _log_action(
    db: Session,
    actor: SuperAdmin,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    *,
    amount: Optional[float] = None,
    payload: Optional[dict] = None,
) -> None:
    sig = sign_admin_decision(
        actor_id=str(actor.id),
        action=action,
        resource_id=resource_id or "",
        decision="executed",
        amount=amount,
    )
    db.add(AdminActionLog(
        actor_kind="super_admin",
        actor_id=str(actor.id),
        actor_level=4,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        amount=amount,
        currency="USD" if amount is not None else None,
        payload=payload,
        signature=sig,
    ))
