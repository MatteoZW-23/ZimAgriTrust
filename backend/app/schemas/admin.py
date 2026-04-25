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
    avg_trust_score: float = 0.0
    escrow_total: float = 0.0
    avg_settlement_hours: float | None = None
    stats: dict = {}
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


class TransactionSummaryResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    product_type: str
    amount: float
    status: str
    buyer_name: str
    seller_name: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TransactionDetailResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    product_type: str
    quantity: float
    total_amount: float
    platform_fee: float
    seller_payout: float
    status: str
    buyer_name: str
    seller_name: str
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    created_at: str
    ledger_history: list[dict] = []

    model_config = ConfigDict(from_attributes=True)


class AgentSummaryResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    region: str
    status: str
    rating: float
    current_load: int
    avg_response_time: float
    specialization: str

    model_config = ConfigDict(from_attributes=True)


class AgentAssignmentResponse(BaseModel):
    id: uuid.UUID
    type: str 
    target_id: uuid.UUID
    status: str
    priority: int
    assigned_at: str
    deadline: str | None

    model_config = ConfigDict(from_attributes=True)


class AgentDetailResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    agent_code: str
    status: str
    region: str
    rating: float
    wallet_balance: float
    pending_earnings: float
    assignments: list[AgentAssignmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConfigUpdate(BaseModel):
    value: str
    is_active: bool = True

class ConfigResponse(BaseModel):
    key: str
    value: str
    group: str
    config_type: str
    is_active: bool
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class UserGrowthData(BaseModel):
    date: str
    count: int

class ProductTrend(BaseModel):
    product: str
    volume: float
    order_count: int

class GeoDistribution(BaseModel):
    province: str
    user_count: int
    volume: float
