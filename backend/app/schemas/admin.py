import uuid
from pydantic import BaseModel, ConfigDict


class AdminOverviewResponse(BaseModel):
    users: int
    farmers: int = 0
    buyers: int = 0
    agents: int = 0
    listings: int
    total_volume: float = 0.0
    platform_revenue: float = 0.0
    pending_verifications: int
    suspended_listings: int
    open_disputes: int
    resolved_disputes: int
    system_health: dict = {}


class ListingReviewResponse(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    farmer_name: str
    farmer_phone: str
    product_type: str
    quantity: float
    grade: str
    location: str
    price_per_unit: float
    status: str
    verification_status: str
    notes: str | None
    offer_count: int

    model_config = ConfigDict(from_attributes=True)


class RiskWatchResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    role: str
    trust_score: float
    risk_score: float
    is_suspended: bool
    status: str
    flags: list[str] = []

    model_config = ConfigDict(from_attributes=True)
