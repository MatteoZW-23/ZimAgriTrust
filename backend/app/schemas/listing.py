import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

from app.models.listing import ListingStatus, OfferStatus, Sector, LogisticsType


class ListingCreate(BaseModel):
    sector: Sector
    product_type: str = Field(min_length=2, max_length=50)
    product_subtype: Optional[str] = Field(default=None, max_length=50)
    grade: Optional[str] = Field(default=None, max_length=20)
    quantity: float = Field(gt=0)
    quantity_unit: str = Field(default="kg")
    price_per_unit: float = Field(gt=0)
    currency: str = Field(default="USD")
    location_province: Optional[str] = Field(default=None, max_length=50)
    location_district: Optional[str] = Field(default=None, max_length=50)
    pickup_address: Optional[str] = Field(default=None)
    
    # New Quality Fields
    is_perishable: bool = Field(default=False)
    expiry_date: Optional[date] = Field(default=None)
    harvest_date: Optional[date] = Field(default=None)
    storage_requirements: Optional[str] = Field(default=None, max_length=100)


class OfferCreate(BaseModel):
    quantity: float = Field(gt=0)
    offered_price: float = Field(gt=0)
    currency: str = Field(default="USD")
    logistics_type: LogisticsType = Field(default=LogisticsType.PLATFORM)
    buyer_message: Optional[str] = Field(default=None, max_length=500)


class CounterOfferRequest(BaseModel):
    counter_price: float = Field(gt=0)


class OfferResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    quantity: float
    offered_price: float
    currency: str
    logistics_type: LogisticsType
    status: OfferStatus
    buyer_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    sector: Sector
    product_type: str
    product_subtype: Optional[str]
    grade: Optional[str]
    quantity: float
    quantity_unit: str
    price_per_unit: float
    currency: str
    location_province: Optional[str]
    location_district: Optional[str]
    status: ListingStatus
    verification_status: str
    
    # Masked Seller Intelligence
    seller_name: str
    seller_trust_score: int
    seller_phone_masked: str
    
    created_at: datetime

    
    # New Quality Fields
    is_perishable: bool
    expiry_date: Optional[date]
    harvest_date: Optional[date]
    storage_requirements: Optional[str]
    
    offers: List[OfferResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TradeMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    is_formal_offer: bool = Field(default=False)
    offer_payload: Optional[dict] = Field(default=None)


class TradeMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_formal_offer: bool
    offer_payload: Optional[dict]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class TradeSessionResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    status: str
    messages: List[TradeMessageResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuyerRequestCreate(BaseModel):
    product_type: str = Field(min_length=2, max_length=50)
    quantity_required: float = Field(gt=0)
    quantity_unit: str = Field(default="kg")
    target_price: float = Field(gt=0)
    currency: str = Field(default="USD")
    delivery_location: Optional[str] = Field(default=None, max_length=100)
    deadline: Optional[datetime] = Field(default=None)


class FarmerResponseCreate(BaseModel):
    supply_quantity: float = Field(gt=0)
    bid_price: float = Field(gt=0)
    currency: str = Field(default="USD")


class FarmerResponseResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    farmer_id: uuid.UUID
    supply_quantity: float
    bid_price: float
    currency: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuyerRequestResponse(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    product_type: str
    quantity_required: float
    quantity_unit: str
    target_price: float
    currency: str
    delivery_location: Optional[str]
    deadline: Optional[datetime]
    status: str
    created_at: datetime
    responses: List[FarmerResponseResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
