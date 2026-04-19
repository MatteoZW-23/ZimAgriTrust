import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.transaction import Order, OrderStatus, Transaction
from app.models.user import User, UserRole
from app.schemas.transaction import DeliveryConfirmRequest, OrderResponse, TransactionResponse

router = APIRouter()


@router.get("", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Order]:
    if current_user.role == UserRole.BUYER:
        return db.query(Order).filter(Order.buyer_id == current_user.id).all()
    elif current_user.role == UserRole.FARMER:
        return db.query(Order).filter(Order.seller_id == current_user.id).all()
    else:
        return db.query(Order).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if current_user.role != UserRole.ADMIN and order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order


@router.post("/{order_id}/confirm-delivery", response_model=OrderResponse)
def confirm_order_delivery(
    order_id: uuid.UUID,
    payload: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.ESCROW_HELD:
        raise HTTPException(status_code=400, detail="Order not in escrow")

    # Finalize order via formal Escrow Release (Moves money to Seller)
    from app.services.escrow_service import release_payment
    try:
        updated_order = release_payment(db, order, handover_code=payload.handover_code)
        return updated_order
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settlement Failure: {str(e)}")


@router.get("/{order_id}/transactions", response_model=List[TransactionResponse])
def get_order_transactions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[Transaction]:
    return db.query(Transaction).filter(Transaction.order_id == order_id).all()


@router.get("/{order_id}/receipt")
def download_order_receipt(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AgriTrust Spec: Digital Receipt Engine.
    Generates and downloads a formal PDF receipt.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization
    if current_user.role != UserRole.ADMIN and order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.services.receipt_service import receipt_service
    from fastapi.responses import FileResponse
    
    try:
        pdf_path = receipt_service.generate_receipt_pdf(order)
        return FileResponse(
            path=pdf_path, 
            filename=f"AgriTrust_Receipt_{order.order_number}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate receipt: {str(e)}")
