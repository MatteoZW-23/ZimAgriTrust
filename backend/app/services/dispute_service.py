import uuid
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
    
    dispute = Dispute(**payload.model_dump())
    db.add(dispute)
    order.status = OrderStatus.DISPUTED
    db.commit()
    db.refresh(dispute)

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
        if reporter.id == order.buyer_id:
            order.status = OrderStatus.REFUNDED
        else:
            order.status = OrderStatus.COMPLETED
            
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
        
        # AgriTrust standard: Platform fee is taken from the total escrow if released, 
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

dispute_core = DisputeService()
