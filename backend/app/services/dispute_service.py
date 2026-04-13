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

    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = payload.resolution

    order = dispute.order
    if payload.release_to_farmer:
        order.status = OrderStatus.COMPLETED
        # Enterprise: Realize the platform commission to Admin Dashboard
        _record_platform_commission(db, order)
    else:
        order.status = OrderStatus.REFUNDED

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

    # If both parties accept, finalize the order adjustment
    if dispute.buyer_accepted and dispute.seller_accepted:
        order = dispute.order
        order.status = OrderStatus.SETTLED
        order.refunded_amount = dispute.proposed_refund_amount
        order.total_amount -= dispute.proposed_refund_amount # New base total
        dispute.status = DisputeStatus.RESOLVED
        
    db.commit()
    db.refresh(dispute)
    return dispute
