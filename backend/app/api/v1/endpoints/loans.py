"""Loan endpoints — spec §3.15 (functions 337-348).

Routes:
  GET    /loans/products                  list active loan products            (F#339)
  POST   /loans/calculate                 amortization calculator               (F#340)
  GET    /loans/eligibility               check eligibility                     (F#337)
  POST   /loans/apply                     apply for a loan                      (F#338)
  GET    /loans/me                        list my loans                         (F#343)
  GET    /loans/{id}                      view loan status                      (F#341)
  POST   /loans/{id}/repay                make a repayment                      (F#342)

Agent:
  POST   /loans/{id}/agent/verify         submit purpose + viability            (F#345, F#346)

Admin:
  POST   /loans/products                  create loan product
  POST   /loans/{id}/admin/approve        approve & disburse                    (F#347, F#344)
  POST   /loans/{id}/admin/reject         reject with reason                    (F#348)
  POST   /loans/{id}/admin/assign-agent   assign an agent for verification
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.loan import Loan, LoanProduct, LoanStatus
from app.models.user import User, UserRole
from app.schemas.loan import (
    LoanAgentVerifyRequest,
    LoanApplyRequest,
    LoanApproveRequest,
    LoanEligibilityResponse,
    LoanProductCreate,
    LoanProductResponse,
    LoanRejectRequest,
    LoanRepayRequest,
    LoanRepaymentCalcRequest,
    LoanRepaymentCalcResponse,
    LoanRepaymentResponse,
    LoanResponse,
)
from app.services.loan_service import loan_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Catalog & calculators (F#337, F#339, F#340)
# ---------------------------------------------------------------------------
@router.get("/products", response_model=list[LoanProductResponse])
def list_products(db: Session = Depends(get_db)) -> list[LoanProduct]:
    """F#339 — list active loan products."""
    return loan_service.list_products(db)


@router.post("/products", response_model=LoanProductResponse, status_code=201)
def create_product(
    payload: LoanProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> LoanProduct:
    """Admin: register a new loan product."""
    if db.query(LoanProduct).filter(LoanProduct.code == payload.code).first():
        raise HTTPException(status_code=409, detail=f"Product code {payload.code!r} already exists")
    product = LoanProduct(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.post("/calculate", response_model=LoanRepaymentCalcResponse)
def calculate(payload: LoanRepaymentCalcRequest) -> dict:
    """F#340 — repayment calculator."""
    return loan_service.calculate_repayment(
        amount_usd=payload.amount_usd,
        annual_rate=payload.annual_rate,
        term_months=payload.term_months,
    )


@router.get("/eligibility", response_model=LoanEligibilityResponse)
def get_eligibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoanEligibilityResponse:
    """F#337 — check loan eligibility for the current user."""
    res = loan_service.check_eligibility(db, current_user)
    return LoanEligibilityResponse(
        eligible=res.eligible,
        max_amount_usd=res.max_amount_usd,
        reasons=res.reasons,
        products=res.products,
    )


# ---------------------------------------------------------------------------
# Application & lifecycle (F#338, F#341, F#342, F#343, F#344)
# ---------------------------------------------------------------------------
@router.post("/apply", response_model=LoanResponse, status_code=201)
def apply_for_loan(
    payload: LoanApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """F#338 — submit a loan application."""
    return loan_service.apply(
        db=db,
        user=current_user,
        product_id=payload.product_id,
        amount_usd=payload.amount_usd,
        term_months=payload.term_months,
        purpose_text=payload.purpose_text,
    )


@router.get("/me", response_model=list[LoanResponse])
def my_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Loan]:
    """F#343 — view my loan history."""
    return loan_service.list_for_user(db, current_user)


def _get_loan_or_404(db: Session, loan_id: uuid.UUID) -> Loan:
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """F#341 — loan status. Borrower, assigned agent, or admin can view."""
    loan = _get_loan_or_404(db, loan_id)
    if (
        loan.user_id != current_user.id
        and loan.agent_id != current_user.id
        and current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return loan


@router.post("/{loan_id}/repay", response_model=LoanRepaymentResponse)
def repay_loan(
    loan_id: uuid.UUID,
    payload: LoanRepayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """F#342 — make a wallet-funded repayment."""
    loan = _get_loan_or_404(db, loan_id)
    if loan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the borrower can repay")
    return loan_service.repay(db, loan, payload.amount_usd)


# ---------------------------------------------------------------------------
# Agent verification (F#345, F#346)
# ---------------------------------------------------------------------------
@router.post("/{loan_id}/agent/verify", response_model=LoanResponse)
def agent_submit_verification(
    loan_id: uuid.UUID,
    payload: LoanAgentVerifyRequest,
    db: Session = Depends(get_db),
    agent: User = Depends(require_roles(UserRole.AGENT)),
) -> Loan:
    loan = _get_loan_or_404(db, loan_id)
    return loan_service.submit_agent_verification(
        db=db,
        loan=loan,
        agent=agent,
        verified_purpose=payload.verified_purpose,
        assessed_viable=payload.assessed_viable,
        notes=payload.notes,
    )


# ---------------------------------------------------------------------------
# Admin approval / rejection / assignment (F#347, F#348)
# ---------------------------------------------------------------------------
@router.post("/{loan_id}/admin/assign-agent", response_model=LoanResponse)
def admin_assign_agent(
    loan_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> Loan:
    loan = _get_loan_or_404(db, loan_id)
    agent = db.query(User).filter(User.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return loan_service.assign_agent(db, loan, agent)


@router.post("/{loan_id}/admin/approve", response_model=LoanResponse)
def admin_approve(
    loan_id: uuid.UUID,
    payload: LoanApproveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Loan:
    """F#347 — admin approves; auto-disburses to wallet (F#344)."""
    loan = _get_loan_or_404(db, loan_id)
    return loan_service.approve(db, loan, admin, payload.notes)


@router.post("/{loan_id}/admin/reject", response_model=LoanResponse)
def admin_reject(
    loan_id: uuid.UUID,
    payload: LoanRejectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Loan:
    """F#348 — admin rejects with reason."""
    loan = _get_loan_or_404(db, loan_id)
    return loan_service.reject(db, loan, admin, payload.reason)
