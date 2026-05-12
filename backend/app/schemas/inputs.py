"""Pydantic schemas for the input marketplace."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Categories ----------

class InputCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    description: Optional[str] = None
    requires_registration: bool
    requires_expiry: bool
    requires_agent_verification: bool
    is_regulated: bool
    is_active: bool


class InputCategoryUpsert(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    requires_registration: bool = False
    requires_expiry: bool = False
    requires_agent_verification: bool = True
    is_regulated: bool = False
    is_active: bool = True


# ---------- Listings ----------

class InputListingCreate(BaseModel):
    category_id: int
    product_name: str
    quantity: float = Field(gt=0)
    price_per_unit: float = Field(gt=0)
    unit: str = "unit"
    brand: Optional[str] = None
    description: Optional[str] = None
    photos: Optional[list[str]] = None
    documents: Optional[list[str]] = None
    expiry_date: Optional[datetime] = None
    registration_number: Optional[str] = None
    location: Optional[str] = None
    province: Optional[str] = None
    min_order_quantity: float = Field(default=1, gt=0)
    currency: str = "USD"


class InputListingUpdate(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = None
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    min_order_quantity: Optional[float] = Field(default=None, gt=0)
    location: Optional[str] = None
    province: Optional[str] = None
    photos: Optional[list[str]] = None
    documents: Optional[list[str]] = None
    expiry_date: Optional[datetime] = None
    registration_number: Optional[str] = None


class InputListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    seller_id: UUID
    category_id: int
    product_name: str
    brand: Optional[str]
    description: Optional[str]
    quantity: float
    unit: str
    price_per_unit: float
    currency: str
    min_order_quantity: float
    location: Optional[str]
    province: Optional[str]
    photos: Optional[list[str]] = None
    documents: Optional[list[str]] = None
    expiry_date: Optional[datetime]
    registration_number: Optional[str]
    status: str
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]
    is_boosted: bool
    boost_paid_until: Optional[datetime]
    view_count: int
    created_at: datetime
    updated_at: datetime


# ---------- Verification ----------

class InputVerificationDecisionIn(BaseModel):
    approve: bool
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


# ---------- Offers ----------

class InputOfferCreate(BaseModel):
    offered_price_per_unit: float = Field(gt=0)
    quantity: float = Field(gt=0)
    note: Optional[str] = None


class InputOfferDecisionIn(BaseModel):
    delivery_address: Optional[str] = None
    reason: Optional[str] = None


class InputOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    listing_id: UUID
    buyer_id: UUID
    offered_price_per_unit: float
    quantity: float
    total_amount: float
    currency: str
    note: Optional[str]
    status: str
    decided_at: Optional[datetime]
    decision_notes: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime


# ---------- Orders ----------

class InputOrderShipIn(BaseModel):
    tracking_number: Optional[str] = None


class InputOrderConfirmIn(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    review: Optional[str] = None


class InputOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_number: str
    offer_id: UUID
    listing_id: UUID
    seller_id: UUID
    buyer_id: UUID
    quantity: float
    unit_price: float
    subtotal: float
    platform_fee: float
    escrow_fee: float
    total_amount: float
    seller_payout: float
    currency: str
    status: str
    is_bulk: bool
    delivery_address: Optional[str]
    tracking_number: Optional[str]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    review_rating: Optional[int]
    review_text: Optional[str]
    created_at: datetime


# ---------- Reports + alerts ----------

class InputReportIn(BaseModel):
    reason: str = Field(pattern="^(fake|expired|mislabelled|unregistered|other)$")
    details: Optional[str] = None
    evidence_urls: Optional[list[str]] = None


class InputReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    listing_id: UUID
    reporter_id: UUID
    reason: str
    details: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime


class InputReportResolveIn(BaseModel):
    uphold: bool
    notes: Optional[str] = None
    remove_listing: bool = False


class InputPriceAlertIn(BaseModel):
    target_price: float = Field(gt=0)
    listing_id: Optional[UUID] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None


class InputPriceAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    target_price: float
    listing_id: Optional[UUID]
    category_id: Optional[int]
    brand: Optional[str]
    is_active: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime
