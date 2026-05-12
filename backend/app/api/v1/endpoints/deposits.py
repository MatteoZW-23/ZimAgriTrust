"""
Buyer deposit endpoints — mounted at `/api/v1/deposits`.

Implements the 12 buyer deposit functions (#348-359):
  - View balance              → existing /payments/wallet
  - Deposit via EcoCash        → POST /deposits/mobile-money
  - Deposit via OneMoney       → POST /deposits/mobile-money
  - Deposit via Bank Transfer  → POST /deposits/bank
  - Deposit via Cash (agent)   → POST /deposits/cash
  - View deposit history       → GET  /deposits
  - Auto top-up rule           → PUT  /deposits/auto-rule
  - Recurring schedule         → POST /deposits/recurring
  - View limits                → GET  /deposits/limits
  - Request refund             → POST /deposits/refunds
  - Link payment method        → POST /deposits/payment-methods
  - View receipts              → GET  /deposits/{id}/receipt
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.deposits import (
    AutoDepositRule,
    DepositChannel,
    DepositIntent,
    DepositLimit,
    DepositRefundRequest,
    PaymentMethod,
    RecurrenceCadence,
    RecurringDepositSchedule,
)
from app.models.user import User, UserRole
from app.schemas.deposit import (
    AgentCollectIn,
    AutoDepositRuleIn,
    AutoDepositRuleOut,
    BankDepositIn,
    CashAgentDepositIn,
    DepositConfirmIn,
    DepositIntentOut,
    DepositLimitOut,
    MobileMoneyDepositIn,
    PaymentMethodCreate,
    PaymentMethodOut,
    RecurringDepositIn,
    RecurringDepositOut,
    RefundDecisionIn,
    RefundRequestIn,
    RefundRequestOut,
)
from app.services import deposit_automation_service, deposit_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Payment methods (function 358)
# ---------------------------------------------------------------------------

@router.post("/payment-methods", response_model=PaymentMethodOut, status_code=201)
def link_payment_method(
    body: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.is_default:
        db.query(PaymentMethod).filter(PaymentMethod.user_id == current_user.id).update(
            {"is_default": False}
        )
    pm = PaymentMethod(
        user_id=current_user.id,
        channel=DepositChannel(body.channel),
        label=body.label,
        last4=body.last4,
        token=body.token,
        extra=body.extra,
        is_default=body.is_default,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


@router.get("/payment-methods", response_model=list[PaymentMethodOut])
def list_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(PaymentMethod)
        .filter(PaymentMethod.user_id == current_user.id)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        .all()
    )


@router.delete("/payment-methods/{pm_id}", status_code=204)
def remove_payment_method(
    pm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pm = db.query(PaymentMethod).filter(
        PaymentMethod.id == pm_id, PaymentMethod.user_id == current_user.id
    ).first()
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")
    db.delete(pm)
    db.commit()


# ---------------------------------------------------------------------------
# Limits + quote (function 356)
# ---------------------------------------------------------------------------

@router.get("/limits", response_model=list[DepositLimitOut])
def get_limits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(DepositLimit).all()


@router.get("/quote")
def deposit_quote(
    amount: float,
    currency: str = "USD",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pre-flight: returns tier, limits, usage, and ID-verification requirement."""
    return deposit_service.check_deposit_allowed(db, user=current_user, amount=amount, currency=currency)


# ---------------------------------------------------------------------------
# Deposit channels (functions 349-352)
# ---------------------------------------------------------------------------

@router.post("/mobile-money")
def deposit_mobile_money(
    body: MobileMoneyDepositIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deposit_service.initiate_mobile_money(
        db,
        user=current_user,
        channel=DepositChannel(body.channel),
        amount=body.amount,
        msisdn=body.msisdn,
        payment_method_id=body.payment_method_id,
    )


@router.post("/bank")
def deposit_bank(
    body: BankDepositIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deposit_service.initiate_bank_transfer(
        db, user=current_user, amount=body.amount, payment_method_id=body.payment_method_id,
    )


@router.post("/cash")
def deposit_cash(
    body: CashAgentDepositIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deposit_service.initiate_cash_via_agent(
        db, user=current_user, amount=body.amount, agent_id=body.agent_id,
    )


# Provider webhook (idempotent). NOTE: in prod, validate provider HMAC before calling.
@router.post("/{intent_id}/confirm")
def confirm_intent(
    intent_id: uuid.UUID,
    body: DepositConfirmIn,
    db: Session = Depends(get_db),
):
    intent = deposit_service.confirm_intent(
        db, intent_id=intent_id, external_reference=body.external_reference,
    )
    return {"status": intent.status.value, "intent_id": str(intent.id)}


# ---------------------------------------------------------------------------
# Cash-via-agent flow (agent endpoints)
# ---------------------------------------------------------------------------

@router.post("/{intent_id}/agent/collect", response_model=DepositIntentOut)
def agent_collect(
    intent_id: uuid.UUID,
    body: AgentCollectIn,
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    return deposit_service.agent_collect_cash(
        db, intent_id=intent_id, agent=agent, receipt_no=body.receipt_no,
    )


@router.post("/{intent_id}/agent/reconcile", response_model=DepositIntentOut)
def agent_reconcile(
    intent_id: uuid.UUID,
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    return deposit_service.agent_reconcile_cash(db, intent_id=intent_id, agent=agent)


# ---------------------------------------------------------------------------
# Admin bank-transfer reconciliation
# ---------------------------------------------------------------------------

class _BankReconcileIn(DepositConfirmIn):
    """Reuses external_reference field (bank statement reference)."""


@router.post("/{intent_id}/bank/reconcile")
def bank_reconcile(
    intent_id: uuid.UUID,
    body: DepositConfirmIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER)),
):
    """Admin marks a bank-transfer intent as cleared, crediting the buyer's wallet."""
    intent = db.query(DepositIntent).filter(DepositIntent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    if intent.channel != DepositChannel.BANK_TRANSFER:
        raise HTTPException(status_code=400, detail="Not a bank-transfer intent")
    intent.bank_reference = body.external_reference
    db.flush()
    confirmed = deposit_service.confirm_intent(
        db, intent_id=intent_id, external_reference=intent.external_reference, actor=actor,
    )
    return {"status": confirmed.status.value, "intent_id": str(confirmed.id)}


@router.get("/admin/pending-bank")
def list_pending_bank_intents(
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER)),
):
    """Admin queue: bank-transfer intents awaiting reconciliation."""
    return [
        {
            "id": str(i.id),
            "user_id": str(i.user_id),
            "amount": float(i.amount),
            "currency": i.currency,
            "external_reference": i.external_reference,
            "bank_reference": i.bank_reference,
            "created_at": i.created_at,
        }
        for i in (
            db.query(DepositIntent)
            .filter(
                DepositIntent.channel == DepositChannel.BANK_TRANSFER,
                DepositIntent.status == "pending",
            )
            .order_by(DepositIntent.created_at.asc())
            .limit(500)
            .all()
        )
    ]


# ---------------------------------------------------------------------------
# History + receipts (functions 353, 359)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[DepositIntentOut])
def list_deposits(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(DepositIntent).filter(DepositIntent.user_id == current_user.id)
    if status_filter:
        q = q.filter(DepositIntent.status == status_filter)
    return q.order_by(DepositIntent.created_at.desc()).limit(limit).all()


@router.get("/{intent_id}/receipt")
def get_receipt(
    intent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    intent = db.query(DepositIntent).filter(
        DepositIntent.id == intent_id, DepositIntent.user_id == current_user.id
    ).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Deposit not found")
    return {
        "intent_id": str(intent.id),
        "user_id": str(intent.user_id),
        "channel": intent.channel.value,
        "amount": float(intent.amount),
        "currency": intent.currency,
        "status": intent.status.value,
        "reference": intent.external_reference,
        "completed_at": intent.completed_at,
        "refundable_until": intent.refundable_until,
        "issuer": "ZimAgriTrust",
    }


# ---------------------------------------------------------------------------
# Auto top-up (function 354)
# ---------------------------------------------------------------------------

@router.put("/auto-rule", response_model=AutoDepositRuleOut)
def upsert_auto_rule(
    body: AutoDepositRuleIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = deposit_automation_service.upsert_auto_rule(
        db,
        user=current_user,
        payment_method_id=body.payment_method_id,
        threshold_usd=body.threshold_usd,
        topup_amount_usd=body.topup_amount_usd,
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/auto-rule", response_model=Optional[AutoDepositRuleOut])
def get_auto_rule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(AutoDepositRule).filter(AutoDepositRule.user_id == current_user.id).first()


@router.delete("/auto-rule", status_code=204)
def disable_auto_rule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deposit_automation_service.disable_auto_rule(db, user=current_user)
    db.commit()


# ---------------------------------------------------------------------------
# Recurring deposits (function 355)
# ---------------------------------------------------------------------------

@router.post("/recurring", response_model=RecurringDepositOut, status_code=201)
def create_recurring(
    body: RecurringDepositIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sched = deposit_automation_service.create_schedule(
        db,
        user=current_user,
        payment_method_id=body.payment_method_id,
        amount_usd=body.amount_usd,
        cadence=RecurrenceCadence(body.cadence),
        day_of_week=body.day_of_week,
        day_of_month=body.day_of_month,
    )
    db.commit()
    db.refresh(sched)
    return sched


@router.get("/recurring", response_model=list[RecurringDepositOut])
def list_recurring(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(RecurringDepositSchedule)
        .filter(RecurringDepositSchedule.user_id == current_user.id)
        .order_by(RecurringDepositSchedule.created_at.desc())
        .all()
    )


@router.delete("/recurring/{schedule_id}", status_code=204)
def cancel_recurring(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deposit_automation_service.cancel_schedule(db, user=current_user, schedule_id=schedule_id)
    db.commit()


# ---------------------------------------------------------------------------
# Refunds (function 357)
# ---------------------------------------------------------------------------

@router.post("/refunds", response_model=RefundRequestOut, status_code=201)
def request_refund(
    body: RefundRequestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = deposit_automation_service.request_refund(
        db, user=current_user, intent_id=body.intent_id, reason=body.reason,
    )
    db.commit()
    db.refresh(req)
    return req


@router.get("/refunds", response_model=list[RefundRequestOut])
def list_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(DepositRefundRequest)
        .filter(DepositRefundRequest.user_id == current_user.id)
        .order_by(DepositRefundRequest.created_at.desc())
        .all()
    )


@router.post("/refunds/{request_id}/decide", response_model=RefundRequestOut)
def decide_refund(
    request_id: uuid.UUID,
    body: RefundDecisionIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.REGIONAL_MANAGER)),
):
    req = deposit_automation_service.decide_refund(
        db, request_id=request_id, actor=actor, approve=body.approve, notes=body.notes,
    )
    db.commit()
    db.refresh(req)
    return req
