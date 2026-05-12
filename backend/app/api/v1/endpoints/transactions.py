import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.transaction import Order, OrderStatus, Transaction
from app.models.user import User, UserRole
from app.models.review import TradeReview
from app.schemas.review import TradeReviewCreate, TradeReviewResponse
from app.schemas.transaction import DeliveryConfirmRequest, OrderResponse, TransactionResponse

# --- Clean architecture (v2) wiring ----------------------------------------
from app.api.v1.dependencies import get_confirm_delivery, get_get_order
from app.application.orders import (
    ConfirmDelivery,
    ConfirmDeliveryCommand,
    GetOrder,
    GetOrderQuery,
    OrderView,
)
from app.application.orders.confirm_delivery import OrderNotFound as ConfirmOrderNotFound
from app.application.orders.get_order import OrderNotFound as GetOrderNotFound
from app.domain.orders.exceptions import (
    InvalidHandoverCode,
    InvalidStatusTransition,
    NotEscrowed,
    OrderDomainError,
    UnauthorizedActor,
)
# ---------------------------------------------------------------------------

router = APIRouter()


# --- Domain-error -> HTTP translator (single place) -------------------------
def _raise_http_for_domain_error(exc: OrderDomainError) -> None:
    if isinstance(exc, UnauthorizedActor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, NotEscrowed):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, InvalidHandoverCode):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, InvalidStatusTransition):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


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
    
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and order.buyer_id != current_user.id and order.seller_id != current_user.id:
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


@router.post("/{order_id}/review", response_model=TradeReviewResponse)
def submit_order_review(
    order_id: uuid.UUID,
    payload: TradeReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeReview:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.id not in {order.buyer_id, order.seller_id}:
        raise HTTPException(status_code=403, detail="Only trade parties can submit reviews")

    if order.status not in {OrderStatus.COMPLETED, OrderStatus.SETTLED}:
        raise HTTPException(status_code=400, detail="Reviews are only allowed for completed/settled orders")

    existing = db.query(TradeReview).filter(
        TradeReview.order_id == order_id,
        TradeReview.reviewer_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Review already submitted for this order")

    reviewee_id = order.seller_id if current_user.id == order.buyer_id else order.buyer_id
    reviewee = db.query(User).filter(User.id == reviewee_id).first()
    if not reviewee:
        raise HTTPException(status_code=404, detail="Review target not found")

    review = TradeReview(
        order_id=order.id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        rating=payload.rating,
        comment=payload.comment,
        reviewer_role=current_user.role.value if current_user.role else None,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Trust incentives from your verification system: apply positive rating rewards.
    if payload.rating >= 4:
        from app.services.verification_service import verification_service
        verification_service.record_positive_rating(db, reviewee, current_user.role)

    return review


@router.get("/{order_id}/reviews", response_model=List[TradeReviewResponse])
def list_order_reviews(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradeReview]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and current_user.id not in {order.buyer_id, order.seller_id}:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(TradeReview).filter(TradeReview.order_id == order_id).order_by(TradeReview.created_at.desc()).all()


@router.get("/{order_id}/receipt")
def download_order_receipt(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ZimAgritrust Spec: Digital Receipt Engine.
    Generates and downloads a formal PDF receipt.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.services.receipt_service import receipt_service
    from fastapi.responses import FileResponse
    
    try:
        pdf_path = receipt_service.generate_receipt_pdf(order)
        return FileResponse(
            path=pdf_path, 
            filename=f"ZimAgritrust_Receipt_{order.order_number}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate receipt: {str(e)}")


# ── Transport Survey ───────────────────────────────────────────────────────────

class TransportSurveyPayload(BaseModel):
    transport_method: str  # own_vehicle, friend_family, local_taxi, cooperative, platform_driver
    transport_cost_usd: Optional[float] = None
    distance_km: Optional[float] = None
    would_use_platform_transport: Optional[bool] = None
    satisfaction_rating: Optional[int] = None  # 1-5
    notes: Optional[str] = None


@router.post("/{order_id}/transport-survey")
def submit_transport_survey(
    order_id: uuid.UUID,
    payload: TransportSurveyPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Post-delivery survey — buyer reports how goods were transported.
    Captures off-platform transport data for market intelligence.
    """
    from pydantic import BaseModel as _BM
    from app.models.transaction import TransportSurvey

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can submit this survey")

    if order.status not in {OrderStatus.COMPLETED, OrderStatus.SETTLED}:
        raise HTTPException(status_code=400, detail="Survey only available after delivery is confirmed")

    existing = db.query(TransportSurvey).filter(TransportSurvey.order_id == order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Survey already submitted for this order")

    survey = TransportSurvey(
        order_id=order_id,
        submitted_by=current_user.id,
        transport_method=payload.transport_method,
        transport_cost_usd=payload.transport_cost_usd,
        distance_km=payload.distance_km,
        would_use_platform_transport=payload.would_use_platform_transport,
        satisfaction_rating=payload.satisfaction_rating,
        notes=payload.notes,
    )
    db.add(survey)
    db.commit()
    return {"message": "Survey submitted. Thank you for your feedback.", "order_id": str(order_id)}


# =============================================================================
# v2 endpoints — clean architecture (use cases + ports + adapters)
# These run alongside the legacy endpoints above. Once parity is verified
# and clients migrate, the legacy ones will be deleted.
# =============================================================================

class OrderViewResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    status: str
    total_amount_cents: int
    seller_payout_cents: int
    currency: str
    logistics_type: str
    handover_code_visible: Optional[str] = None
    created_at: str

    @classmethod
    def from_view(cls, v: OrderView) -> "OrderViewResponse":
        return cls(
            id=v.id,
            order_number=v.order_number,
            buyer_id=v.buyer_id,
            seller_id=v.seller_id,
            status=v.status,
            total_amount_cents=v.total_amount_cents,
            seller_payout_cents=v.seller_payout_cents,
            currency=v.currency,
            logistics_type=v.logistics_type,
            handover_code_visible=v.handover_code_visible,
            created_at=v.created_at.isoformat(),
        )


@router.get("/v2/{order_id}", response_model=OrderViewResponse)
def get_order_v2(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetOrder = Depends(get_get_order),
) -> OrderViewResponse:
    try:
        view = use_case(GetOrderQuery(
            order_id=order_id,
            actor_id=current_user.id,
            actor_is_admin=(current_user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}),
        ))
    except GetOrderNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderDomainError as exc:
        _raise_http_for_domain_error(exc)
    return OrderViewResponse.from_view(view)


@router.post("/v2/{order_id}/confirm-delivery", response_model=OrderViewResponse)
def confirm_delivery_v2(
    order_id: uuid.UUID,
    payload: DeliveryConfirmRequest,
    current_user: User = Depends(get_current_user),
    confirm: ConfirmDelivery = Depends(get_confirm_delivery),
    get_view: GetOrder = Depends(get_get_order),
) -> OrderViewResponse:
    try:
        confirm(ConfirmDeliveryCommand(
            order_id=order_id,
            actor_id=current_user.id,
            handover_code=payload.handover_code,
        ))
    except ConfirmOrderNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderDomainError as exc:
        _raise_http_for_domain_error(exc)

    view = get_view(GetOrderQuery(
        order_id=order_id,
        actor_id=current_user.id,
        actor_is_admin=(current_user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}),
    ))
    return OrderViewResponse.from_view(view)
