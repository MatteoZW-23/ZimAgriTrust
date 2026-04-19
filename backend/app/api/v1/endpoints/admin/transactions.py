import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.transaction import Order, Transaction
from app.models.system_audit import SystemAudit
from app.schemas.admin import TransactionSummaryResponse, TransactionDetailResponse

router = APIRouter()

@router.get("", response_model=list[TransactionSummaryResponse])
def list_transactions(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    buyer_id: Optional[uuid.UUID] = None,
    seller_id: Optional[uuid.UUID] = None,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """
    Function 73: View all transactions (Orders) with filtering.
    """
    query = db.query(Order).options(joinedload(Order.buyer), joinedload(Order.seller), joinedload(Order.listing))
    
    if status:
        query = query.filter(Order.status == status.lower())
    if buyer_id:
        query = query.filter(Order.buyer_id == buyer_id)
    if seller_id:
        query = query.filter(Order.seller_id == seller_id)
        
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    
    return [
        TransactionSummaryResponse(
            id=o.id,
            order_number=o.order_number,
            product_type=o.listing.product_type if o.listing else "Unknown",
            amount=o.total_amount,
            status=o.status.value if hasattr(o.status, 'value') else str(o.status),
            buyer_name=o.buyer.full_name if o.buyer else "N/A",
            seller_name=o.seller.full_name if o.seller else "N/A",
            created_at=o.created_at.isoformat()
        )
        for o in orders
    ]

@router.get("/{order_id}", response_model=TransactionDetailResponse)
def get_transaction_detail(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """
    Function 81: View transaction details.
    """
    order = (
        db.query(Order)
        .options(joinedload(Order.buyer), joinedload(Order.seller), joinedload(Order.listing))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # Fetch ledger history
    ledger = db.query(Transaction).filter(Transaction.order_id == order_id).order_by(Transaction.created_at.asc()).all()
    
    return TransactionDetailResponse(
        id=order.id,
        order_number=order.order_number,
        product_type=order.listing.product_type if order.listing else "Unknown",
        quantity=order.quantity,
        total_amount=order.total_amount,
        platform_fee=order.platform_fee,
        seller_payout=order.seller_payout,
        status=order.status.value if hasattr(order.status, 'value') else str(order.status),
        buyer_name=order.buyer.full_name if order.buyer else "N/A",
        seller_name=order.seller.full_name if order.seller else "N/A",
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        created_at=order.created_at.isoformat(),
        ledger_history=[
            {"type": t.type, "amount": t.amount, "status": t.status, "ts": t.created_at.isoformat()}
            for t in ledger
        ]
    )

@router.post("/escrow/{order_id}/force-release")
def force_escrow_release(
    order_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "DELIVERED" 
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="ESCROW_FORCE_RELEASE",
        target_type="ORDER",
        target_id=order.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"status": "Escrow released by Admin", "audit_ref": str(audit.id)}

@router.post("/escrow/{order_id}/force-refund")
def force_escrow_refund(
    order_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "REFUNDED"
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="ESCROW_FORCE_REFUND",
        target_type="ORDER",
        target_id=order.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"status": "Escrow refunded by Admin", "audit_ref": str(audit.id)}
