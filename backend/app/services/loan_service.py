"""Loan service — implements spec §3.15 (functions 337-348).

Encapsulates loan eligibility, amortization math, lifecycle transitions
(submit → agent verification → admin approval → disbursement → repayment),
and integration with the user's wallet.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.loan import (
    Loan,
    LoanProduct,
    LoanPurpose,
    LoanRepayment,
    LoanStatus,
)
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


@dataclass
class EligibilityResult:
    eligible: bool
    max_amount_usd: float
    reasons: List[str]
    products: List[LoanProduct]


def _amortize_monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """Standard amortization formula. Returns monthly payment in USD.

    P * r * (1+r)^n / ((1+r)^n - 1)  where r = monthly rate
    """
    if months <= 0:
        raise ValueError("months must be positive")
    if annual_rate <= 0:
        return round(principal / months, 2)
    r = annual_rate / 12.0
    factor = (1 + r) ** months
    pay = principal * r * factor / (factor - 1)
    return round(pay, 2)


class LoanService:
    # ------------------------------------------------------------------
    # Catalog (F#339)
    # ------------------------------------------------------------------
    @staticmethod
    def list_products(db: Session) -> List[LoanProduct]:
        return db.query(LoanProduct).filter(LoanProduct.is_active.is_(True)).all()

    # ------------------------------------------------------------------
    # Eligibility (F#337)
    # ------------------------------------------------------------------
    @classmethod
    def check_eligibility(cls, db: Session, user: User) -> EligibilityResult:
        reasons: List[str] = []
        if user.role not in (UserRole.FARMER, UserRole.BUYER):
            reasons.append("Only farmers and buyers may apply for loans")
            return EligibilityResult(False, 0.0, reasons, [])
        if not getattr(user, "is_phone_verified", False):
            reasons.append("Phone verification required")
        if not getattr(user, "is_id_verified", False):
            reasons.append("Identity verification required")

        trust = int(user.trust_score or 0)
        all_products = cls.list_products(db)
        eligible_products = [p for p in all_products if trust >= p.min_trust_score]

        max_amount = max((p.max_amount_usd for p in eligible_products), default=0.0)

        if not eligible_products:
            reasons.append(f"Trust score ({trust}) below minimum threshold of any product")

        eligible = not reasons
        return EligibilityResult(
            eligible=eligible,
            max_amount_usd=max_amount,
            reasons=reasons,
            products=eligible_products,
        )

    # ------------------------------------------------------------------
    # Repayment calculator (F#340)
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_repayment(
        amount_usd: float, annual_rate: float, term_months: int
    ) -> dict:
        monthly = _amortize_monthly_payment(amount_usd, annual_rate, term_months)
        total = round(monthly * term_months, 2)
        return {
            "amount_usd": round(amount_usd, 2),
            "annual_rate": annual_rate,
            "term_months": term_months,
            "monthly_payment_usd": monthly,
            "total_repayment_usd": total,
            "total_interest_usd": round(total - amount_usd, 2),
        }

    # ------------------------------------------------------------------
    # Apply (F#338)
    # ------------------------------------------------------------------
    @classmethod
    def apply(
        cls,
        db: Session,
        user: User,
        product_id: uuid.UUID,
        amount_usd: float,
        term_months: int,
        purpose_text: Optional[str] = None,
    ) -> Loan:
        product = db.query(LoanProduct).filter(LoanProduct.id == product_id).first()
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Loan product not found")
        if amount_usd < product.min_amount_usd or amount_usd > product.max_amount_usd:
            raise HTTPException(
                status_code=400,
                detail=f"Amount must be between ${product.min_amount_usd} and ${product.max_amount_usd}",
            )
        if term_months < product.min_term_months or term_months > product.max_term_months:
            raise HTTPException(
                status_code=400,
                detail=f"Term must be between {product.min_term_months} and {product.max_term_months} months",
            )
        if (user.trust_score or 0) < product.min_trust_score:
            raise HTTPException(
                status_code=403,
                detail=f"Trust score below minimum ({product.min_trust_score})",
            )

        # Block multiple active loans (single-loan policy in MVP)
        active = (
            db.query(Loan)
            .filter(
                Loan.user_id == user.id,
                Loan.status.in_(
                    [
                        LoanStatus.SUBMITTED,
                        LoanStatus.AGENT_VERIFICATION,
                        LoanStatus.APPROVED,
                        LoanStatus.DISBURSED,
                        LoanStatus.ACTIVE,
                    ]
                ),
            )
            .first()
        )
        if active:
            raise HTTPException(
                status_code=409,
                detail="You already have an active or pending loan",
            )

        monthly = _amortize_monthly_payment(amount_usd, product.interest_rate_annual, term_months)
        loan = Loan(
            user_id=user.id,
            product_id=product.id,
            amount_usd=round(amount_usd, 2),
            term_months=term_months,
            interest_rate_annual=product.interest_rate_annual,
            monthly_payment_usd=monthly,
            purpose_text=purpose_text,
            status=LoanStatus.SUBMITTED,
            outstanding_principal_usd=round(amount_usd, 2),
        )
        db.add(loan)
        db.commit()
        db.refresh(loan)
        logger.info("loan.submitted user=%s loan=%s amount=%s", user.id, loan.id, amount_usd)
        return loan

    # ------------------------------------------------------------------
    # Agent verification (F#345, F#346)
    # ------------------------------------------------------------------
    @staticmethod
    def assign_agent(db: Session, loan: Loan, agent: User) -> Loan:
        if agent.role != UserRole.AGENT:
            raise HTTPException(status_code=403, detail="Only agents can be assigned")
        if loan.status not in (LoanStatus.SUBMITTED, LoanStatus.AGENT_VERIFICATION):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot assign agent in loan status {loan.status.value}",
            )
        loan.agent_id = agent.id
        loan.status = LoanStatus.AGENT_VERIFICATION
        db.commit()
        db.refresh(loan)
        return loan

    @staticmethod
    def submit_agent_verification(
        db: Session,
        loan: Loan,
        agent: User,
        verified_purpose: bool,
        assessed_viable: bool,
        notes: Optional[str] = None,
    ) -> Loan:
        if loan.agent_id != agent.id:
            raise HTTPException(status_code=403, detail="You are not assigned to this loan")
        loan.agent_verified_purpose = verified_purpose
        loan.agent_assessed_viable = assessed_viable
        loan.agent_notes = notes
        loan.agent_reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(loan)
        return loan

    # ------------------------------------------------------------------
    # Admin approve / reject (F#347, F#348)
    # ------------------------------------------------------------------
    @classmethod
    def approve(cls, db: Session, loan: Loan, approver: User, notes: Optional[str] = None) -> Loan:
        if approver.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can approve loans")
        if loan.status != LoanStatus.AGENT_VERIFICATION:
            raise HTTPException(
                status_code=400,
                detail="Loan must complete agent verification before approval",
            )
        if not (loan.agent_verified_purpose and loan.agent_assessed_viable):
            raise HTTPException(
                status_code=400,
                detail="Agent must verify both purpose and viability before approval",
            )
        loan.status = LoanStatus.APPROVED
        loan.approver_id = approver.id
        loan.approval_notes = notes
        loan.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(loan)
        # Auto-disburse on approval (F#344)
        return cls.disburse(db, loan)

    @staticmethod
    def reject(db: Session, loan: Loan, approver: User, reason: str) -> Loan:
        if approver.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can reject loans")
        if loan.status in (LoanStatus.DISBURSED, LoanStatus.ACTIVE, LoanStatus.REPAID):
            raise HTTPException(status_code=400, detail="Cannot reject a disbursed loan")
        loan.status = LoanStatus.REJECTED
        loan.approver_id = approver.id
        loan.rejection_reason = reason
        loan.rejected_at = datetime.utcnow()
        db.commit()
        db.refresh(loan)
        return loan

    # ------------------------------------------------------------------
    # Disbursement (F#344) — credits user wallet
    # ------------------------------------------------------------------
    @staticmethod
    def disburse(db: Session, loan: Loan) -> Loan:
        if loan.status != LoanStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Loan must be APPROVED to disburse")
        user = db.query(User).filter(User.id == loan.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Borrower not found")
        user.balance_usd = round((user.balance_usd or 0) + loan.amount_usd, 2)
        loan.status = LoanStatus.DISBURSED
        loan.disbursed_at = datetime.utcnow()
        loan.next_due_date = datetime.utcnow() + timedelta(days=30)
        loan.outstanding_principal_usd = loan.amount_usd
        db.commit()
        db.refresh(loan)
        # Move to ACTIVE on next save cycle
        loan.status = LoanStatus.ACTIVE
        db.commit()
        db.refresh(loan)
        return loan

    # ------------------------------------------------------------------
    # Repayment (F#342) — debits wallet
    # ------------------------------------------------------------------
    @staticmethod
    def repay(db: Session, loan: Loan, amount_usd: float) -> LoanRepayment:
        if loan.status not in (LoanStatus.ACTIVE, LoanStatus.DISBURSED):
            raise HTTPException(status_code=400, detail="Loan is not active")
        if amount_usd <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        user = db.query(User).filter(User.id == loan.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Borrower not found")
        if (user.balance_usd or 0) < amount_usd:
            raise HTTPException(status_code=402, detail="Insufficient wallet balance")

        # Split into interest first, principal second.
        monthly_rate = (loan.interest_rate_annual or 0) / 12.0
        interest = round(loan.outstanding_principal_usd * monthly_rate, 2)
        interest_paid = min(interest, amount_usd)
        principal_paid = round(amount_usd - interest_paid, 2)

        user.balance_usd = round((user.balance_usd or 0) - amount_usd, 2)
        loan.total_repaid_usd = round((loan.total_repaid_usd or 0) + amount_usd, 2)
        loan.outstanding_principal_usd = round(
            max(0.0, (loan.outstanding_principal_usd or 0) - principal_paid), 2
        )
        loan.next_due_date = datetime.utcnow() + timedelta(days=30)
        if loan.outstanding_principal_usd <= 0.005:
            loan.status = LoanStatus.REPAID
            loan.outstanding_principal_usd = 0.0

        repayment = LoanRepayment(
            loan_id=loan.id,
            amount_usd=round(amount_usd, 2),
            principal_component_usd=principal_paid,
            interest_component_usd=interest_paid,
            method="WALLET",
        )
        db.add(repayment)
        db.commit()
        db.refresh(repayment)
        db.refresh(loan)
        return repayment

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    @staticmethod
    def list_for_user(db: Session, user: User) -> List[Loan]:
        return (
            db.query(Loan)
            .filter(Loan.user_id == user.id)
            .order_by(Loan.created_at.desc())
            .all()
        )


loan_service = LoanService()
