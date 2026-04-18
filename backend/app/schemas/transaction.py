import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.models.transaction import OrderStatus, TransactionType


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    offer_id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    quantity: float
    total_amount: float
    platform_fee: float
    seller_payout: float
    currency: str
    product: str
    status: OrderStatus
    
    # Conditional Contact Reveal (Masked until Escrow)
    seller_contact_reveal: str
    buyer_contact_reveal: str
    
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: uuid.UUID
    order_id: Optional[uuid.UUID]
    user_id: uuid.UUID
    type: TransactionType
    amount: float
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryConfirmRequest(BaseModel):
    order_number: str
    confirmation_code: Optional[str] = None
