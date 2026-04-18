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
