from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# SUPPLIER REGISTRATION
# ============================================================================

class SupplierApplicationCreate(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    business_type: str = Field(max_length=50)  # agro_dealer, distributor, manufacturer, importer
    years_in_operation: Optional[int] = Field(None, ge=0)
    physical_address: Optional[str] = None
    contact_person: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    product_categories: Optional[List[str]] = None

    # User account fields
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=4, max_length=100)


class SupplierDocumentUpload(BaseModel):
    document_type: str  # certificate_of_incorporation, tax_clearance, trade_license, product_registration, bank_details, store_photos
    document_url: str
    document_name: Optional[str] = None


class SupplierDocumentsSubmit(BaseModel):
    documents: List[SupplierDocumentUpload]


class SupplierApplicationStatusResponse(BaseModel):
    supplier_id: uuid.UUID
    business_name: str
    verification_status: str
    verification_notes: Optional[str] = None
    submitted_documents: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SUPPLIER PROFILE
# ============================================================================

class SupplierProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_name: str
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    business_type: Optional[str] = None
    years_in_operation: Optional[int] = None
    physical_address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    product_categories: Optional[List[str]] = None
    verification_status: str
    rating: float
    total_sales: int
    total_revenue: float
    trust_score: int
    available_balance: float
    pending_balance: float
    lifetime_earnings: float
    shipping_policy: Optional[str] = None
    return_policy: Optional[str] = None
    business_hours: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SupplierProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    physical_address: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    product_categories: Optional[List[str]] = None
    shipping_policy: Optional[str] = None
    return_policy: Optional[str] = None
    business_hours: Optional[str] = Field(None, max_length=200)


# ============================================================================
# SUPPLIER PRODUCTS
# ============================================================================

class SupplierProductCreate(BaseModel):
    product_type: str  # input, machinery
    input_category: Optional[str] = None
    machinery_category: Optional[str] = None
    name: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    price: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=5)
    quantity_available: int = Field(ge=0)
    unit_type: str = Field(default="piece", max_length=20)
    min_stock_level: int = Field(default=5, ge=0)

    # Input-specific
    registration_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    manufacturer: Optional[str] = None
    safety_data_sheet_url: Optional[str] = None

    # Machinery-specific
    condition: Optional[str] = None
    warranty_months: Optional[int] = None
    delivery_included: bool = False
    manual_url: Optional[str] = None

    photo_urls: Optional[List[str]] = None
    status: str = Field(default="draft")


class SupplierProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity_available: Optional[int] = Field(None, ge=0)
    unit_type: Optional[str] = Field(None, max_length=20)
    min_stock_level: Optional[int] = Field(None, ge=0)
    registration_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    manufacturer: Optional[str] = None
    safety_data_sheet_url: Optional[str] = None
    condition: Optional[str] = None
    warranty_months: Optional[int] = None
    delivery_included: Optional[bool] = None
    manual_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    status: Optional[str] = None


class SupplierProductResponse(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    sku: Optional[str] = None
    product_type: str
    input_category: Optional[str] = None
    machinery_category: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    quantity_available: int
    unit_type: str
    min_stock_level: int
    registration_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    manufacturer: Optional[str] = None
    safety_data_sheet_url: Optional[str] = None
    condition: Optional[str] = None
    warranty_months: Optional[int] = None
    delivery_included: bool
    manual_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    status: str
    is_boosted: bool
    is_featured: bool
    view_count: int
    order_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Supplier info (for public views)
    supplier_name: Optional[str] = None
    supplier_rating: Optional[float] = None
    supplier_verification: Optional[str] = None
    supplier_subscription_plan: Optional[str] = None
    supplier_badges: List[str] = []
    visibility_weight: int = 100
    model_config = ConfigDict(from_attributes=True)


class SupplierStockUpdate(BaseModel):
    quantity_available: int = Field(ge=0)
    notes: Optional[str] = None


class BulkPriceUpdate(BaseModel):
    updates: List[Dict[str, Any]]  # [{"product_id": "...", "new_price": 10.0}, ...]


class BoostProductRequest(BaseModel):
    duration_days: int = Field(default=7, ge=1, le=30)


# ============================================================================
# SUPPLIER ORDERS
# ============================================================================

class SupplierOrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    supplier_id: uuid.UUID
    buyer_id: uuid.UUID
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    subtotal: float
    tax_amount: float
    shipping_cost: float
    platform_fee: float
    total_amount: float
    currency: str
    delivery_address: Optional[str] = None
    delivery_phone: Optional[str] = None
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    status: str
    payment_status: str
    promo_code: Optional[str] = None
    promo_discount: float
    buyer_notes: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    model_config = ConfigDict(from_attributes=True)


class TrackingUpdate(BaseModel):
    tracking_number: str = Field(min_length=1, max_length=100)
    shipping_method: Optional[str] = None


class OrderCancelRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


# ============================================================================
# PUBLIC ORDER (BUYER FACING)
# ============================================================================

class PublicOrderItem(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1)


class PublicOrderCreate(BaseModel):
    items: List[PublicOrderItem] = Field(min_length=1)
    delivery_address: str = Field(min_length=5)
    delivery_phone: str = Field(min_length=7, max_length=20)
    shipping_method: Optional[str] = None
    buyer_notes: Optional[str] = None
    promo_code: Optional[str] = None


# ============================================================================
# SUPPLIER WALLET
# ============================================================================

class SupplierWalletResponse(BaseModel):
    available_balance: float
    pending_balance: float
    lifetime_earnings: float
    currency: str = "USD"


class SupplierWithdrawalRequest(BaseModel):
    amount: float = Field(gt=0)
    method: str  # bank_transfer, ecocash, onemoney
    account_details: Optional[str] = None


class SupplierWalletTxnResponse(BaseModel):
    id: uuid.UUID
    txn_type: str
    amount: float
    fee: float
    net_amount: float
    currency: str
    status: str
    withdrawal_method: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ANALYTICS
# ============================================================================

class SalesAnalyticsResponse(BaseModel):
    total_revenue: float
    total_orders: int
    avg_order_value: float
    revenue_by_month: List[Dict[str, Any]]


class BestsellerResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    total_sold: int
    total_revenue: float


class InventoryAnalyticsResponse(BaseModel):
    total_products: int
    in_stock: int
    low_stock: int
    out_of_stock: int
    total_value: float


# ============================================================================
# ADMIN ACTIONS
# ============================================================================

class AdminSupplierAction(BaseModel):
    notes: Optional[str] = None


class AdminCategoryUpdate(BaseModel):
    categories: List[str]


# ============================================================================
# PUBLIC SUPPLIER LIST
# ============================================================================

class PublicSupplierResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    business_type: Optional[str] = None
    logo_url: Optional[str] = None
    rating: float
    total_sales: int
    trust_score: int
    verification_status: str
    subscription_plan: Optional[str] = None
    badges: List[str] = []
    visibility_weight: int = 100
    product_categories: Optional[List[str]] = None
    physical_address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# BULK CSV IMPORT
# ============================================================================

class CSVImportResponse(BaseModel):
    import_id: uuid.UUID
    status: str
    total_rows: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []
    created_at: datetime


class CSVImportError(BaseModel):
    row_number: int
    field: str
    error: str
    value: Optional[str] = None


# ============================================================================
# SUPPLIER REVIEWS
# ============================================================================

class SupplierReviewCreate(BaseModel):
    order_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class SupplierReviewResponse(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    buyer_id: uuid.UUID
    order_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    supplier_response: Optional[str] = None
    supplier_responseed_at: Optional[datetime] = None
    is_flagged: bool
    is_hidden: bool
    created_at: datetime
    # Buyer info (for display)
    buyer_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SupplierReviewUpdate(BaseModel):
    supplier_response: Optional[str] = Field(None, max_length=1000)


class SupplierReviewListResponse(BaseModel):
    reviews: List[SupplierReviewResponse]
    total: int
    average_rating: float
    rating_distribution: Dict[int, int]  # {1: count, 2: count, ...}


# ============================================================================
# SUPPLIER DISCOUNTS/PROMOTIONS
# ============================================================================

class SupplierDiscountCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_type: str = Field(..., description="percentage, fixed_amount, buy_x_get_y")
    discount_value: float = Field(gt=0)
    min_order_value: Optional[float] = Field(None, ge=0)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    applicable_products: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    max_uses: Optional[int] = Field(None, ge=1)
    max_uses_per_user: Optional[int] = Field(None, ge=1)
    start_date: datetime
    end_date: datetime
    description: Optional[str] = Field(None, max_length=500)


class SupplierDiscountUpdate(BaseModel):
    discount_value: Optional[float] = Field(None, gt=0)
    min_order_value: Optional[float] = Field(None, ge=0)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    max_uses: Optional[int] = Field(None, ge=1)
    max_uses_per_user: Optional[int] = Field(None, ge=1)
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)


class SupplierDiscountResponse(BaseModel):
    id: uuid.UUID
    supplier_id: uuid.UUID
    code: str
    discount_type: str
    discount_value: float
    min_order_value: Optional[float] = None
    max_discount_amount: Optional[float] = None
    applicable_products: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    max_uses: Optional[int] = None
    max_uses_per_user: Optional[int] = None
    current_uses: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DiscountValidationRequest(BaseModel):
    code: str
    order_total: float
    product_ids: Optional[List[str]] = None
