import uuid
from typing import Optional
from pydantic import BaseModel, Field

from app.models.dispute import DisputeStatus


class DisputeCreate(BaseModel):
    order_id: uuid.UUID
    type: str = Field(min_length=3, max_length=30)
    description: str = Field(min_length=3, max_length=2000)


class SettlementProposal(BaseModel):
    discount_percent: float = Field(ge=0, le=100)
    memo: str = Field(min_length=10)


class DisputeResolve(BaseModel):
    resolution: str = Field(min_length=5)
    release_to_farmer: bool = False


class DisputeResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    type: str
    description: str
    status: DisputeStatus
    resolution: Optional[str] = None
    
    product: str
    amount: float
    buyer_name: str
    buyer_trust: int
    seller_name: str
    seller_trust: int
    ai_risk: int
    ai_recommendation: str
    
    # Financials
    proposed_discount: float
    proposed_refund_amount: float
    buyer_accepted: bool
    seller_accepted: bool
    agent_resolution_memo: Optional[str] = None

    model_config = {"from_attributes": True}
