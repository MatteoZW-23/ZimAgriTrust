import uuid
from typing import Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.dispute import Dispute, DisputeStatus
from app.models.transaction import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeCreate, DisputeResolve


from app.services.agent_assignment import AgentAssignmentService

def create_dispute(db: Session, payload: DisputeCreate, actor: User) -> Dispute:
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # ... security checks ...
    if actor.role not in {UserRole.ADMIN, UserRole.AGENT} and actor.id not in {order.buyer_id, order.seller_id}:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    dispute_data = payload.model_dump()
    dispute_data["raised_by"] = actor.id
    dispute_data["category"] = dispute_data.get("type", "general")
    dispute_data["title"] = f"Dispute - {dispute_data.get('type', 'General')}"
    dispute = Dispute(**dispute_data)
    db.add(dispute)
    order.status = OrderStatus.DISPUTED
    from app.services.escrow_account_service import EscrowAccountService
    EscrowAccountService.freeze_for_order(db, order, reason=payload.description)
    db.commit()
    db.refresh(dispute)

    # Apply temporary trust freeze/penalty on dispute open for both parties.
    from app.services.verification_service import verification_service
    verification_service.apply_dispute_penalty(db, order.buyer, ruled_against=False)
    verification_service.apply_dispute_penalty(db, order.seller, ruled_against=False)
    from app.services.notification_service import notification_service
    notification_service._send_sms(
        order.buyer.phone_number,
        f"ZimAgritrust: A dispute has been opened for transaction #{order.id}. Your trust score is temporarily impacted pending resolution."
    )
    notification_service._send_sms(
        order.seller.phone_number,
        f"ZimAgritrust: A dispute has been opened for transaction #{order.id}. Your trust score is temporarily impacted pending resolution."
    )

    # Hybrid AI Triage: Auto-resolve or Assign Agent
    _ai_triage_dispute(db, dispute, actor)
    
    return dispute


def _ai_triage_dispute(db: Session, dispute: Dispute, reporter: User):
    """
    Powerful AI Decision Engine:
    - Auto-Settle low value disputes for high-trust users.
    - Escalate complex/high-value disputes to field experts.
    """
    order = dispute.order
    
    # 1. Macro-Threshold: Auto-resolve low-value friction points
    if order.total_amount <= 20.0 and reporter.trust_score >= 85:
        # System favors high-trust user for minor issues to keep platform moving
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = "AI AUTO-SETTLEMENT: Low value / High-trust fast-track."
        
        # Action: Refund if buyer reported, Complete if seller reported (simple favor)
        from app.services.escrow_service import refund_payment, release_payment
        if reporter.id == order.buyer_id:
            refund_payment(db, order)
        else:
            release_payment(db, order)
            
        db.commit()
        return

    # 2. Escalation: High value or Low trust requires human field verification
    assignment_service = AgentAssignmentService(db)
    assignment_service.assign_agent_to_dispute(dispute.id, priority=3)


def resolve_dispute(db: Session, dispute: Dispute, payload: DisputeResolve) -> Dispute:
    if dispute.status == DisputeStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Already resolved")

    from app.services.escrow_service import release_payment, refund_payment
    
    order = dispute.order
    if payload.release_to_farmer:
        # Full Pay to Seller (Diagram 3: FULL PAY)
        release_payment(db, order)
    else:
        # Full Refund to Buyer (Diagram 3: FULL REFUND)
        refund_payment(db, order)

    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = payload.resolution

    # Apply additional trust deduction to losing party on final ruling.
    from app.services.verification_service import verification_service
    losing_user = order.buyer if payload.release_to_farmer else order.seller
    verification_service.apply_dispute_penalty(db, losing_user, ruled_against=True)
    from app.services.notification_service import notification_service
    outcome = "released to farmer" if payload.release_to_farmer else "refunded to buyer"
    notification_service._send_sms(
        order.buyer.phone_number,
        f"ZimAgritrust: Dispute for transaction #{order.id} resolved. Outcome: {outcome}."
    )
    notification_service._send_sms(
        order.seller.phone_number,
        f"ZimAgritrust: Dispute for transaction #{order.id} resolved. Outcome: {outcome}."
    )

    db.commit()
    db.refresh(dispute)
    return dispute


def _record_platform_commission(db: Session, order: Order):
    """
    Ensures platform fees are tracked and sent to the administrative dashboard ledger.
    """
    from app.models.transaction import Transaction, TransactionType
    
    # Track the commission withdrawal from the transaction flow
    commission = Transaction(
        order_id=order.id,
        user_id=order.buyer_id, # Source of funds
        type=TransactionType.FEE,
        amount=order.platform_fee,
        status="completed"
    )
    db.add(commission)


def propose_settlement(db: Session, dispute: Dispute, discount_percent: float, memo: str, agent: User) -> Dispute:
    if agent.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise HTTPException(status_code=403, detail="Only Agents/Admins can propose settlements")
    
    dispute.status = DisputeStatus.PROPOSED_OFFER
    dispute.proposed_discount = discount_percent
    dispute.proposed_refund_amount = (dispute.order.total_amount * (discount_percent / 100))
    dispute.agent_resolution_memo = memo
    
    # Reset acceptances for new proposal
    dispute.buyer_accepted = False
    dispute.seller_accepted = False
    
    db.commit()
    db.refresh(dispute)
    return dispute


def accept_settlement(db: Session, dispute: Dispute, user: User) -> Dispute:
    if user.id == dispute.order.buyer_id:
        dispute.buyer_accepted = True
    elif user.id == dispute.order.seller_id:
        dispute.seller_accepted = True
    else:
        raise HTTPException(status_code=403, detail="Only parties to the order can accept settlements")

    # If both parties accept, finalize the order adjustment (Diagram 3: PARTIAL / SPLIT)
    if dispute.buyer_accepted and dispute.seller_accepted:
        from app.services.escrow_service import resolve_dispute as escrow_resolve
        
        # Calculate split logic based on proposal
        buyer_refund = dispute.proposed_refund_amount
        seller_payout = dispute.order.total_amount - buyer_refund
        
        # ZimAgritrust standard: Platform fee is taken from the total escrow if released, 
        # but in partial disputes, we often adjust it proportionally.
        # For simplicity, we use the original platform fee capped by seller payout.
        fee = min(dispute.order.platform_fee, seller_payout * 0.05) 
        seller_net = seller_payout - fee
        
        escrow_resolve(db, dispute.order, buyer_refund, seller_net, fee)
        
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = f"MUTUAL SETTLEMENT: {dispute.agent_resolution_memo}"
        
    db.commit()
    db.refresh(dispute)
    return dispute


class DisputeService:
    @staticmethod
    def create_dispute(db: Session, payload: DisputeCreate, actor: User) -> Dispute:
        return create_dispute(db, payload, actor)

    @staticmethod
    def resolve_dispute(db: Session, dispute: Dispute, payload: DisputeResolve) -> Dispute:
        return resolve_dispute(db, dispute, payload)

    @staticmethod
    def propose_settlement(db: Session, dispute: Dispute, discount_percent: float, memo: str, agent: User) -> Dispute:
        return propose_settlement(db, dispute, discount_percent, memo, agent)

    @staticmethod
    def accept_settlement(db: Session, dispute: Dispute, user: User) -> Dispute:
        return accept_settlement(db, dispute, user)

    @staticmethod
    def admin_override(db: Session, dispute_id: int, decision: Dict, admin_user: User) -> Dispute:
        """
        Sovereign Admin Override: Direct forced settlement by high-level oversight.
        """
        from app.models.audit_log import AuditLog
        from app.services.escrow_service import resolve_dispute as escrow_resolve
        
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # 1. Execute Escrow Adjustment
        buyer_refund = decision.get("buyer_refund", 0)
        seller_payout = decision.get("seller_payout", 0)
        fee = decision.get("platform_fee", 0)
        
        escrow_resolve(db, dispute.order, buyer_refund, seller_payout, fee)
        
        # 2. Update Dispute Status
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = f"ADMIN OVERSIGHT OVERRIDE: {decision.get('reason', 'Manual Override')}"
        
        # 3. Log the Audit Event
        audit = AuditLog(
            admin_id=admin_user.id,
            action="DISPUTE_OVERRIDE",
            resource_type="DISPUTE",
            resource_id=str(dispute_id),
            details=decision
        )
        db.add(audit)
        
        db.commit()
        db.refresh(dispute)
        return dispute

dispute_core = DisputeService()
