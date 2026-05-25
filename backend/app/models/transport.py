"""
Transport system models for ZimAgriTrust.
Implements transport requests, negotiations, quotes, driver assignments, deliveries, tracking, payment allocations, settlements, and disputes.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Enum, Float, ForeignKey, String, Text, DateTime, Boolean, JSON, Integer, Numeric, BigInteger
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class SqliteCompatibleARRAY(TypeDecorator):
    """Allows PostgreSQL ARRAY type on postgres, fallback to JSON/Text on SQLite."""
    impl = JSON
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON)



# ── Enums ────────────────────────────────────────────────────────────────────────

class TransportMode(str, enum.Enum):
    PLATFORM_DELIVERY_BUYER_REQUESTED = "PLATFORM_DELIVERY_BUYER_REQUESTED"
    PLATFORM_DELIVERY_FARMER_REQUESTED = "PLATFORM_DELIVERY_FARMER_REQUESTED"
    SELF_PICKUP = "SELF_PICKUP"
    SELF_DELIVERY = "SELF_DELIVERY"
    NEGOTIATED_TRANSPORT = "NEGOTIATED_TRANSPORT"
    DEFERRED = "DEFERRED"


class TransportRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    PRICING = "PRICING"
    PRICED = "PRICED"
    ASSIGNING = "ASSIGNING"
    ASSIGNED = "ASSIGNED"
    IN_NEGOTIATION = "IN_NEGOTIATION"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class TransportQuoteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class NegotiationStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    COUNTER_OFFER = "COUNTER_OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ADMIN_REVIEW = "ADMIN_REVIEW"
    RESOLVED = "RESOLVED"


class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    OFFER = "OFFER"
    COUNTER_OFFER = "COUNTER_OFFER"
    ACCEPTANCE = "ACCEPTANCE"
    REJECTION = "REJECTION"
    SYSTEM = "SYSTEM"


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    DRIVER_EN_ROUTE = "DRIVER_EN_ROUTE"
    AT_PICKUP = "AT_PICKUP"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    AT_DELIVERY = "AT_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TrackingStatus(str, enum.Enum):
    MOVING = "MOVING"
    STOPPED = "STOPPED"
    IDLE = "IDLE"


class AllocationType(str, enum.Enum):
    GOODS_PAYMENT = "GOODS_PAYMENT"
    TRANSPORT_FEE = "TRANSPORT_FEE"
    PLATFORM_FEE = "PLATFORM_FEE"
    REFUND = "REFUND"


class AllocationStatus(str, enum.Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class SettlementType(str, enum.Enum):
    FARMER_PAYOUT = "FARMER_PAYOUT"
    DRIVER_PAYOUT = "DRIVER_PAYOUT"
    BUYER_REFUND = "BUYER_REFUND"


class SettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


# ── Transport Request ─────────────────────────────────────────────────────────────

class TransportRequest(Base):
    """Transport request for an order"""
    __tablename__ = "transport_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    requested_by: Mapped[str] = mapped_column(String(20), nullable=False)  # 'BUYER' or 'FARMER'
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    mode: Mapped[TransportMode] = mapped_column(Enum(TransportMode), nullable=False)
    
    # Pickup details
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    pickup_longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    pickup_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pickup_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Delivery details
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    delivery_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Cargo details
    cargo_weight: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cargo_volume: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    cargo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_handling: Mapped[Optional[List[str]]] = mapped_column(SqliteCompatibleARRAY(String), nullable=True)
    
    # Timing
    preferred_pickup_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preferred_delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    urgency_level: Mapped[str] = mapped_column(String(20), default="STANDARD", nullable=False)
    
    # Vehicle preferences
    preferred_vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vehicle_requirements: Mapped[Optional[List[str]]] = mapped_column(SqliteCompatibleARRAY(String), nullable=True)
    
    # Status
    status: Mapped[TransportRequestStatus] = mapped_column(Enum(TransportRequestStatus), default=TransportRequestStatus.PENDING, nullable=False)
    decision_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_made_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_made_by: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Versioning
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="transport_request")
    quotes = relationship("TransportQuote", back_populates="transport_request", cascade="all, delete-orphan")
    negotiations = relationship("TransportNegotiation", back_populates="transport_request", cascade="all, delete-orphan")
    driver_assignments = relationship("DriverAssignment", back_populates="transport_request", cascade="all, delete-orphan")


# ── Transport Quote ───────────────────────────────────────────────────────────────

class TransportQuote(Base):
    """Transport quote with pricing breakdown"""
    __tablename__ = "transport_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transport_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Pricing components
    base_fee: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    distance_km: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    per_km_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    distance_fee: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    weight_fee: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    volume_fee: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    urgency_multiplier: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, nullable=False)
    urgency_fee: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    rural_surcharge: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    peak_surcharge: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    weather_surcharge: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    # Vehicle pricing
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_base_fee: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    vehicle_per_km_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    
    # Totals
    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[TransportQuoteStatus] = mapped_column(Enum(TransportQuoteStatus), default=TransportQuoteStatus.ACTIVE, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Pricing metadata
    pricing_algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    pricing_version: Mapped[str] = mapped_column(String(20), nullable=False)
    pricing_factors: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    transport_request = relationship("TransportRequest", back_populates="quotes")


# ── Transport Negotiation ─────────────────────────────────────────────────────────

class TransportNegotiation(Base):
    """Transport fee negotiation between buyer and farmer"""
    __tablename__ = "transport_negotiations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    transport_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True)
    
    initiator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    counterparty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    status: Mapped[NegotiationStatus] = mapped_column(Enum(NegotiationStatus), default=NegotiationStatus.INITIATED, nullable=False)
    
    # Timing
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Final agreement
    final_payer: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'BUYER', 'FARMER', 'SPLIT'
    final_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    split_ratio: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"buyer": 0.6, "farmer": 0.4}
    
    # Escalation
    escalated_to_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin_resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    transport_request = relationship("TransportRequest", back_populates="negotiations")
    messages = relationship("NegotiationMessage", back_populates="negotiation", cascade="all, delete-orphan")


# ── Negotiation Message ────────────────────────────────────────────────────────────

class NegotiationMessage(Base):
    """Message in transport negotiation"""
    __tablename__ = "negotiation_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    negotiation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transport_negotiations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_offer: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    negotiation = relationship("TransportNegotiation", back_populates="messages")


# ── Driver Assignment ─────────────────────────────────────────────────────────────

class DriverAssignment(Base):
    """Driver assignment for transport request"""
    __tablename__ = "driver_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transport_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(20), nullable=False)  # 'AUTO', 'ADMIN', 'MANUAL'
    assigned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    status: Mapped[AssignmentStatus] = mapped_column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED, nullable=False)
    
    # Driver response
    driver_response_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    driver_rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vehicle details
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_registration: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Estimates
    estimated_distance_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    route_polyline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing
    transport_fee: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    platform_commission: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    driver_earnings: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    transport_request = relationship("TransportRequest", back_populates="driver_assignments")
    delivery = relationship("Delivery", back_populates="driver_assignment", uselist=False)


# ── Delivery ───────────────────────────────────────────────────────────────────────

class Delivery(Base):
    """Delivery tracking for an order"""
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("driver_assignments.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    
    # Pickup confirmation
    pickup_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    pickup_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    pickup_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_signature_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Delivery confirmation
    delivery_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    delivery_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    delivery_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_signature_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_of_delivery_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Current location
    current_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    current_longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    last_location_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # ETA tracking
    estimated_arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Delay handling
    delay_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delay_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    failed_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="delivery")
    driver_assignment = relationship("DriverAssignment", back_populates="delivery")
    tracking_points = relationship("DeliveryTracking", back_populates="delivery", cascade="all, delete-orphan")


# ── Delivery Tracking ─────────────────────────────────────────────────────────────

class DeliveryTracking(Base):
    """GPS tracking points for delivery"""
    __tablename__ = "delivery_tracking"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Location
    latitude: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(11, 8), nullable=False)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    altitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Movement
    speed_kmh: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    heading_degrees: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[TrackingStatus] = mapped_column(Enum(TrackingStatus), nullable=False)
    
    # Device info
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    delivery = relationship("Delivery", back_populates="tracking_points")


# ── Payment Allocation ─────────────────────────────────────────────────────────────

class PaymentAllocation(Base):
    """Payment allocation for goods, transport, platform fees, refunds"""
    __tablename__ = "payment_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    transport_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True)
    
    allocation_type: Mapped[AllocationType] = mapped_column(Enum(AllocationType), nullable=False)
    payer: Mapped[str] = mapped_column(String(20), nullable=False)  # 'BUYER', 'FARMER', 'PLATFORM'
    payee: Mapped[str] = mapped_column(String(20), nullable=False)  # 'FARMER', 'DRIVER', 'PLATFORM', 'BUYER'
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Payment method
    payment_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status tracking
    status: Mapped[AllocationStatus] = mapped_column(Enum(AllocationStatus), default=AllocationStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    held_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Failure/Refund reasons
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # External payment IDs
    external_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


# ── Settlement ────────────────────────────────────────────────────────────────────

class Settlement(Base):
    """Settlement for farmer payouts, driver payouts, buyer refunds"""
    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    settlement_type: Mapped[SettlementType] = mapped_column(Enum(SettlementType), nullable=False)
    
    # Amounts
    gross_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    deductions: Mapped[dict] = mapped_column(JSON, nullable=False)
    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Breakdown
    goods_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    transport_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    platform_fee_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    other_deductions: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    # Payout method
    payout_method: Mapped[str] = mapped_column(String(30), nullable=False)
    payout_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status tracking
    status: Mapped[SettlementStatus] = mapped_column(Enum(SettlementStatus), default=SettlementStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Failure handling
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # External transaction
    external_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


# ── Dispute ────────────────────────────────────────────────────────────────────────

class TransportDispute(Base):
    """Dispute for orders, transport, or delivery"""
    __tablename__ = "transport_disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    transport_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True)
    delivery_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("deliveries.id", ondelete="SET NULL"), nullable=True)
    
    raised_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Dispute details
    dispute_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Amount in dispute
    disputed_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Status
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    
    # Resolution
    resolution_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Escalation
    escalated_to_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Deadlines
    response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    evidence = relationship("TransportDisputeEvidence", back_populates="dispute", cascade="all, delete-orphan")


# ── Dispute Evidence ───────────────────────────────────────────────────────────────

class TransportDisputeEvidence(Base):
    """Evidence files for transport disputes"""
    __tablename__ = "transport_dispute_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transport_disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    dispute = relationship("TransportDispute", back_populates="evidence")
