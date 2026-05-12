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


# ---------------------------------------------------------------------------
# Listing extras: edit, photos, boost, stats, save, report  (F#52-58, F#92, F#94)
# ---------------------------------------------------------------------------
class ListingUpdate(BaseModel):
    """Partial update for a listing. F#53."""
    product_subtype: Optional[str] = Field(default=None, max_length=50)
    grade: Optional[str] = Field(default=None, max_length=20)
    quantity: Optional[float] = Field(default=None, gt=0)
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    location_province: Optional[str] = Field(default=None, max_length=50)
    location_district: Optional[str] = Field(default=None, max_length=50)
    pickup_address: Optional[str] = Field(default=None)
    is_perishable: Optional[bool] = None
    expiry_date: Optional[date] = None
    harvest_date: Optional[date] = None
    storage_requirements: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ListingPhotosUpdate(BaseModel):
    """Add photo URLs to a listing. F#52."""
    urls: List[str] = Field(default_factory=list)


class ListingPhotosResponse(BaseModel):
    listing_id: uuid.UUID
    photo_urls: List[str]


class ListingBoostRequest(BaseModel):
    """F#57. $2 default; admin may configure tiers in future."""
    duration_days: int = Field(default=7, ge=1, le=30)


class ListingBoostResponse(BaseModel):
    listing_id: uuid.UUID
    is_boosted: bool
    boosted_until: Optional[datetime]
    boost_fee: float
    wallet_balance: float


class ListingStatsResponse(BaseModel):
    """F#56."""
    listing_id: uuid.UUID
    view_count: int
    offer_count: int
    accepted_offer_count: int
    days_active: int
    is_boosted: bool


class SavedListingResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingReportCreate(BaseModel):
    """F#94."""
    reason: str = Field(min_length=1, max_length=40)
    details: Optional[str] = Field(default=None, max_length=2000)


class ListingReportResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    reporter_id: uuid.UUID
    reason: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    # F#52, F#56, F#57, F#58
    view_count: int = 0
    photo_urls: Optional[List[str]] = None
    is_boosted: bool = False
    boosted_until: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    offers: List[OfferResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ListingSearchItem(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    sector: Sector
    product_type: str
    product_subtype: Optional[str]
    crop: Optional[str]
    grade: Optional[str]
    quantity: float
    quantity_unit: str
    price_per_unit: float
    currency: str
    location_province: Optional[str]
    location_district: Optional[str]
    location: Optional[str]
    status: ListingStatus
    verification_status: str
    seller_name: str
    seller_trust_score: int
    seller_phone_masked: str
    created_at: datetime
    is_perishable: bool
    expiry_date: Optional[date]
    harvest_date: Optional[date]
    storage_requirements: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int
    has_more: bool


class ListingSearchResponse(BaseModel):
    success: bool = True
    data: List[ListingSearchItem] = Field(default_factory=list)
    pagination: PaginationMeta


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
