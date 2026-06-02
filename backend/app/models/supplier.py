import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer,
    Numeric, String, Text, JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


# ============================================================================
# ENUMS
# ============================================================================

class SupplierBusinessType(str, enum.Enum):
    AGRO_DEALER = "agro_dealer"
    DISTRIBUTOR = "distributor"
    MANUFACTURER = "manufacturer"
    IMPORTER = "importer"


class SupplierVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SupplierProductType(str, enum.Enum):
    INPUT = "input"
    MACHINERY = "machinery"


class InputCategory(str, enum.Enum):
    SEEDS = "seeds"
    FERTILIZER = "fertilizer"
    PESTICIDES = "pesticides"
    HERBICIDES = "herbicides"
    FUNGICIDES = "fungicides"
    ANIMAL_FEED = "animal_feed"


class MachineryCategory(str, enum.Enum):
    TRACTOR = "tractor"
    SPRAYER = "sprayer"
    IRRIGATION = "irrigation"
    TILLER = "tiller"
    HARVESTER = "harvester"
    TOOLS = "tools"


class ProductCondition(str, enum.Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"


class SupplierProductStatus(str, enum.Enum):
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    DRAFT = "draft"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SupplierOrderStatus(str, enum.Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


SUPPLIER_ORDER_STATUS_TRANSITIONS: dict[SupplierOrderStatus, set[SupplierOrderStatus]] = {
    SupplierOrderStatus.NEW: {SupplierOrderStatus.CONFIRMED, SupplierOrderStatus.CANCELLED},
    SupplierOrderStatus.CONFIRMED: {SupplierOrderStatus.PROCESSING, SupplierOrderStatus.SHIPPED, SupplierOrderStatus.CANCELLED},
    SupplierOrderStatus.PROCESSING: {SupplierOrderStatus.SHIPPED, SupplierOrderStatus.CANCELLED},
    SupplierOrderStatus.SHIPPED: {SupplierOrderStatus.DELIVERED, SupplierOrderStatus.CANCELLED},
    SupplierOrderStatus.DELIVERED: set(),
    SupplierOrderStatus.CANCELLED: {SupplierOrderStatus.REFUNDED},
    SupplierOrderStatus.REFUNDED: set(),
}


def can_transition_supplier_order_status(
    current: SupplierOrderStatus, next_status: SupplierOrderStatus
) -> bool:
    return next_status in SUPPLIER_ORDER_STATUS_TRANSITIONS.get(current, set())


class SupplierPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    ESCROW = "escrow"
    PAID = "paid"
    REFUNDED = "refunded"


class SupplierWalletTxnType(str, enum.Enum):
    SALE = "sale"
    WITHDRAWAL = "withdrawal"
    PLATFORM_FEE = "platform_fee"
    REFUND = "refund"
    BOOST_FEE = "boost_fee"
    ADJUSTMENT = "adjustment"


# ============================================================================
# SUPPLIER PROFILE TABLE
# ============================================================================

class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Business details
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_type: Mapped[Optional[SupplierBusinessType]] = mapped_column(
        Enum(SupplierBusinessType, values_callable=_enum_values, name="supplierbusinesstype"),
        nullable=True
    )
    years_in_operation: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    physical_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    product_categories: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["seeds", "fertilizer", ...]

    # Verification
    verification_status: Mapped[SupplierVerificationStatus] = mapped_column(
        Enum(SupplierVerificationStatus, values_callable=_enum_values, name="supplierverificationstatus"),
        default=SupplierVerificationStatus.PENDING
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Performance
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    trust_score: Mapped[int] = mapped_column(Integer, default=60)

    # Wallet
    available_balance: Mapped[float] = mapped_column(Float, default=0.0)
    pending_balance: Mapped[float] = mapped_column(Float, default=0.0)
    lifetime_earnings: Mapped[float] = mapped_column(Float, default=0.0)

    # Subscription
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # basic, pro, enterprise
    subscription_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # active, past_due, cancelled, suspended, trial
    subscription_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Policies
    shipping_policy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    return_policy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_hours: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="supplier_profile")
    documents = relationship("SupplierDocument", back_populates="supplier", cascade="all, delete-orphan")
    products = relationship("SupplierProduct", back_populates="supplier", cascade="all, delete-orphan")
    orders = relationship("SupplierOrder", back_populates="supplier", cascade="all, delete-orphan")
    wallet_transactions = relationship("SupplierWalletTransaction", back_populates="supplier", cascade="all, delete-orphan")


# ============================================================================
# SUPPLIER DOCUMENTS TABLE
# ============================================================================

class SupplierDocument(Base):
    __tablename__ = "supplier_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # certificate_of_incorporation, tax_clearance, trade_license, product_registration, bank_details, store_photos
    document_url: Mapped[str] = mapped_column(String(500), nullable=False)
    document_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("SupplierProfile", back_populates="documents")


# ============================================================================
# SUPPLIER PRODUCT TABLE
# ============================================================================

class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)

    # Type & Category
    product_type: Mapped[SupplierProductType] = mapped_column(
        Enum(SupplierProductType, values_callable=_enum_values, name="supplierproducttype"),
        nullable=False
    )
    input_category: Mapped[Optional[InputCategory]] = mapped_column(
        Enum(InputCategory, values_callable=_enum_values, name="supplierinputcategory"),
        nullable=True
    )
    machinery_category: Mapped[Optional[MachineryCategory]] = mapped_column(
        Enum(MachineryCategory, values_callable=_enum_values, name="suppliermachinerycategory"),
        nullable=True
    )

    # Core details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    quantity_available: Mapped[int] = mapped_column(Integer, default=0)
    unit_type: Mapped[str] = mapped_column(String(20), default="piece")  # kg, litre, bag, piece
    min_stock_level: Mapped[int] = mapped_column(Integer, default=5)

    # Input-specific fields
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    safety_data_sheet_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Machinery-specific fields
    condition: Mapped[Optional[ProductCondition]] = mapped_column(
        Enum(ProductCondition, values_callable=_enum_values, name="supplierproductcondition"),
        nullable=True
    )
    warranty_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delivery_included: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Media
    photo_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Up to 5 images

    # Status
    status: Mapped[SupplierProductStatus] = mapped_column(
        Enum(SupplierProductStatus, values_callable=_enum_values, name="supplierproductstatus"),
        default=SupplierProductStatus.DRAFT
    )

    # Boost & Promotion
    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_fee: Mapped[float] = mapped_column(Float, default=0.0)
    boosted_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    order_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    supplier = relationship("SupplierProfile", back_populates="products")
    order_items = relationship("SupplierOrderItem", back_populates="product")
    stock_history = relationship("SupplierStockHistory", back_populates="product", cascade="all, delete-orphan")


# ============================================================================
# SUPPLIER ORDER TABLE
# ============================================================================

class SupplierOrder(Base):
    __tablename__ = "supplier_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Financials
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    platform_fee: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(5), default="USD")

    # Delivery
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Logistics Integration
    logistics_delivery_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True, deferred=True
    )

    # Status
    status: Mapped[SupplierOrderStatus] = mapped_column(
        Enum(SupplierOrderStatus, values_callable=_enum_values, name="supplierorderstatus"),
        default=SupplierOrderStatus.NEW
    )
    payment_status: Mapped[SupplierPaymentStatus] = mapped_column(
        Enum(SupplierPaymentStatus, values_callable=_enum_values, name="supplierpaymentstatus"),
        default=SupplierPaymentStatus.PENDING
    )

    # Promo
    promo_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    promo_discount: Mapped[float] = mapped_column(Float, default=0.0)

    # Notes
    buyer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    supplier = relationship("SupplierProfile", back_populates="orders")
    buyer = relationship("User", foreign_keys=[buyer_id])
    items = relationship("SupplierOrderItem", back_populates="order", cascade="all, delete-orphan")


class SupplierOrderItem(Base):
    __tablename__ = "supplier_order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_orders.id"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)  # snapshot
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    order = relationship("SupplierOrder", back_populates="items")
    product = relationship("SupplierProduct", back_populates="order_items")


# ============================================================================
# SUPPLIER STOCK HISTORY TABLE
# ============================================================================

class SupplierStockHistory(Base):
    __tablename__ = "supplier_stock_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_products.id"), nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # restock, sale, adjustment
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # order id, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("SupplierProduct", back_populates="stock_history")


# ============================================================================
# SUPPLIER WALLET TRANSACTIONS TABLE
# ============================================================================

class SupplierWalletTransaction(Base):
    __tablename__ = "supplier_wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_orders.id"), nullable=True)
    txn_type: Mapped[SupplierWalletTxnType] = mapped_column(
        Enum(SupplierWalletTxnType, values_callable=_enum_values, name="supplierwallettxntype"),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="completed")  # completed, pending, failed
    withdrawal_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # bank_transfer, ecocash, onemoney
    reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("SupplierProfile", back_populates="wallet_transactions")


# ============================================================================
# SUPPLIER CSV IMPORT HISTORY TABLE
# ============================================================================

class SupplierCSVImport(Base):
    __tablename__ = "supplier_csv_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, completed, failed, partial
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    successful: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of errors
    rollback_performed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    supplier = relationship("SupplierProfile")


# ============================================================================
# SUPPLIER REVIEWS TABLE
# ============================================================================

class SupplierReview(Base):
    __tablename__ = "supplier_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_orders.id"), nullable=False, index=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Supplier response
    supplier_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_responseed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Moderation
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    supplier = relationship("SupplierProfile")
    buyer = relationship("User", foreign_keys=[buyer_id])
    order = relationship("SupplierOrder")


# ============================================================================
# SUPPLIER DISCOUNTS/PROMOTIONS TABLE
# ============================================================================

class SupplierDiscount(Base):
    __tablename__ = "supplier_discounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier_profiles.id"), nullable=False, index=True)
    
    # Discount details
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # Promo code
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # percentage, fixed_amount, buy_x_get_y
    discount_value: Mapped[float] = mapped_column(Float, nullable=False)  # Percentage or fixed amount
    
    # Applicability
    min_order_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Minimum order value to apply discount
    max_discount_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Maximum discount amount
    applicable_products: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of product IDs
    applicable_categories: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of categories
    
    # Usage limits
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Maximum total uses
    max_uses_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Maximum uses per user
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    
    # Validity
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Additional info
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    supplier = relationship("SupplierProfile")
