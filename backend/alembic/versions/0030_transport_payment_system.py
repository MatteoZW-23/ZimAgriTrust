"""Transport payment system tables.

Revision ID: 0030
Revises: 0029
Create Date: 2026-05-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


TRANSPORT_MODE_ENUM = sa.Enum(
    "PLATFORM_DELIVERY_BUYER_REQUESTED",
    "PLATFORM_DELIVERY_FARMER_REQUESTED",
    "SELF_PICKUP",
    "SELF_DELIVERY",
    "NEGOTIATED_TRANSPORT",
    "DEFERRED",
    name="transportmode",
)

TRANSPORT_REQUEST_STATUS_ENUM = sa.Enum(
    "PENDING", "PRICING", "PRICED", "ASSIGNING", "ASSIGNED",
    "IN_NEGOTIATION", "ACCEPTED", "REJECTED", "CANCELLED", "COMPLETED",
    name="transportrequeststatus",
)

TRANSPORT_QUOTE_STATUS_ENUM = sa.Enum(
    "ACTIVE", "ACCEPTED", "EXPIRED", "CANCELLED",
    name="transportquotestatus",
)

NEGOTIATION_STATUS_ENUM = sa.Enum(
    "INITIATED", "COUNTER_OFFER", "ACCEPTED", "REJECTED",
    "CANCELLED", "EXPIRED", "ADMIN_REVIEW", "RESOLVED",
    name="negotiationstatus",
)

MESSAGE_TYPE_ENUM = sa.Enum(
    "TEXT", "OFFER", "COUNTER_OFFER", "ACCEPTANCE", "REJECTION", "SYSTEM",
    name="negotiationmessagetype",
)

ASSIGNMENT_STATUS_ENUM = sa.Enum(
    "ASSIGNED", "ACCEPTED", "REJECTED", "CANCELLED", "COMPLETED",
    name="driverassignmentstatus",
)

DELIVERY_STATUS_ENUM = sa.Enum(
    "PENDING", "ASSIGNED", "DRIVER_EN_ROUTE", "AT_PICKUP", "PICKED_UP",
    "IN_TRANSIT", "AT_DELIVERY", "DELIVERED", "CANCELLED", "FAILED",
    name="deliverystatus",
)

TRACKING_STATUS_ENUM = sa.Enum(
    "MOVING", "STOPPED", "IDLE",
    name="trackingstatus",
)

ALLOCATION_TYPE_ENUM = sa.Enum(
    "GOODS_PAYMENT", "TRANSPORT_FEE", "PLATFORM_FEE", "REFUND",
    name="paymentallocationtype",
)

ALLOCATION_STATUS_ENUM = sa.Enum(
    "PENDING", "HELD", "RELEASED", "FAILED", "REFUNDED",
    name="paymentallocationstatus",
)

SETTLEMENT_TYPE_ENUM = sa.Enum(
    "FARMER_PAYOUT", "DRIVER_PAYOUT", "BUYER_REFUND",
    name="settlementtype",
)

SETTLEMENT_STATUS_ENUM = sa.Enum(
    "PENDING", "PROCESSING", "COMPLETED", "FAILED",
    name="settlementstatus",
)

DISPUTE_STATUS_ENUM = sa.Enum(
    "OPEN", "UNDER_REVIEW", "RESOLVED", "CLOSED", "ESCALATED",
    name="disputestatus",
)

NOTIFICATION_STATUS_ENUM = sa.Enum(
    "PENDING", "SENT", "DELIVERED", "FAILED", "READ",
    name="notificationstatus",
)


def upgrade() -> None:
    # Create enums
    TRANSPORT_MODE_ENUM.create(op.get_bind(), checkfirst=True)
    TRANSPORT_REQUEST_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    TRANSPORT_QUOTE_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    NEGOTIATION_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    MESSAGE_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    ASSIGNMENT_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    DELIVERY_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    TRACKING_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    ALLOCATION_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    ALLOCATION_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    SETTLEMENT_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    SETTLEMENT_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    DISPUTE_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    NOTIFICATION_STATUS_ENUM.create(op.get_bind(), checkfirst=True)

    # Add transport columns to orders table
    op.add_column('orders', sa.Column('transport_responsible_party', sa.String(20), nullable=True))
    op.add_column('orders', sa.Column('transport_mode', TRANSPORT_MODE_ENUM, nullable=True))
    op.add_column('orders', sa.Column('transport_fee', sa.Numeric(15, 2), server_default='0', nullable=False))
    op.add_column('orders', sa.Column('transport_fee_payer', sa.String(20), nullable=True))
    
    # Create transport_requests table
    op.create_table(
        "transport_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("requested_by", sa.String(20), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("mode", TRANSPORT_MODE_ENUM, nullable=False),
        sa.Column("pickup_address", sa.String(), nullable=False),
        sa.Column("pickup_latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("pickup_longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("pickup_contact_name", sa.String(100), nullable=True),
        sa.Column("pickup_contact_phone", sa.String(20), nullable=True),
        sa.Column("delivery_address", sa.String(), nullable=False),
        sa.Column("delivery_latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("delivery_longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("delivery_contact_name", sa.String(100), nullable=True),
        sa.Column("delivery_contact_phone", sa.String(20), nullable=True),
        sa.Column("cargo_weight", sa.Numeric(10, 2), nullable=False),
        sa.Column("cargo_volume", sa.Numeric(10, 2), nullable=True),
        sa.Column("cargo_description", sa.String(), nullable=True),
        sa.Column("special_handling", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_pickup_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_delivery_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("urgency_level", sa.String(20), server_default='STANDARD', nullable=False),
        sa.Column("preferred_vehicle_type", sa.String(50), nullable=True),
        sa.Column("vehicle_requirements", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", TRANSPORT_REQUEST_STATUS_ENUM, server_default='PENDING', nullable=False),
        sa.Column("decision_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_made_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_made_by", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_transport_requests_requested_by", "transport_requests", ["requested_by"])
    op.create_index("idx_transport_requests_status", "transport_requests", ["status"])
    op.create_index("idx_transport_requests_created_at", "transport_requests", ["created_at"])
    op.create_index("idx_transport_requests_decision_deadline", "transport_requests", ["decision_deadline"])

    # Create transport_quotes table
    op.create_table(
        "transport_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("transport_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("base_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("distance_km", sa.Numeric(10, 2), nullable=False),
        sa.Column("per_km_rate", sa.Numeric(10, 4), nullable=False),
        sa.Column("distance_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("weight_fee", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("volume_fee", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("urgency_multiplier", sa.Numeric(5, 4), server_default='1.0', nullable=False),
        sa.Column("urgency_fee", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("rural_surcharge", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("peak_surcharge", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("weather_surcharge", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("vehicle_type", sa.String(50), nullable=False),
        sa.Column("vehicle_base_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("vehicle_per_km_rate", sa.Numeric(10, 4), nullable=False),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default='USD', nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", TRANSPORT_QUOTE_STATUS_ENUM, server_default='ACTIVE', nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pricing_algorithm", sa.String(100), nullable=False),
        sa.Column("pricing_version", sa.String(20), nullable=False),
        sa.Column("pricing_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_transport_quotes_status", "transport_quotes", ["status"])
    op.create_index("idx_transport_quotes_valid_until", "transport_quotes", ["valid_until"])
    op.create_index("idx_transport_quotes_created_at", "transport_quotes", ["created_at"])

    # Create transport_negotiations table
    op.create_table(
        "transport_negotiations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("transport_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("initiator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("counterparty_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", NEGOTIATION_STATUS_ENUM, server_default='INITIATED', nullable=False),
        sa.Column("initiated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_payer", sa.String(20), nullable=True),
        sa.Column("final_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("split_ratio", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("escalated_to_admin", sa.Boolean(), server_default='false', nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("admin_resolution", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_transport_negotiations_initiator_id", "transport_negotiations", ["initiator_id"])
    op.create_index("idx_transport_negotiations_status", "transport_negotiations", ["status"])
    op.create_index("idx_transport_negotiations_expires_at", "transport_negotiations", ["expires_at"])

    # Create negotiation_messages table
    op.create_table(
        "negotiation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("negotiation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_negotiations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("message_type", MESSAGE_TYPE_ENUM, nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("structured_offer", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_negotiation_messages_sender_id", "negotiation_messages", ["sender_id"])
    op.create_index("idx_negotiation_messages_created_at", "negotiation_messages", ["created_at"])

    # Create driver_assignments table
    op.create_table(
        "driver_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("transport_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_by", sa.String(20), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", ASSIGNMENT_STATUS_ENUM, server_default='ASSIGNED', nullable=False),
        sa.Column("driver_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("driver_rejection_reason", sa.String(), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vehicle_type", sa.String(50), nullable=False),
        sa.Column("vehicle_registration", sa.String(20), nullable=False),
        sa.Column("estimated_distance_km", sa.Numeric(10, 2), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("route_polyline", sa.String(), nullable=True),
        sa.Column("transport_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("platform_commission", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("driver_earnings", sa.Numeric(15, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_driver_assignments_driver_id", "driver_assignments", ["driver_id"])
    op.create_index("idx_driver_assignments_status", "driver_assignments", ["status"])
    op.create_index("idx_driver_assignments_assigned_at", "driver_assignments", ["assigned_at"])

    # Create deliveries table
    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("driver_assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("driver_assignments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", DELIVERY_STATUS_ENUM, server_default='PENDING', nullable=False),
        sa.Column("pickup_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pickup_confirmed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("pickup_code", sa.String(10), nullable=True),
        sa.Column("pickup_photo_url", sa.String(), nullable=True),
        sa.Column("pickup_signature_url", sa.String(), nullable=True),
        sa.Column("pickup_notes", sa.String(), nullable=True),
        sa.Column("delivery_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_confirmed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("delivery_code", sa.String(10), nullable=True),
        sa.Column("delivery_photo_url", sa.String(), nullable=True),
        sa.Column("delivery_signature_url", sa.String(), nullable=True),
        sa.Column("delivery_notes", sa.String(), nullable=True),
        sa.Column("proof_of_delivery_url", sa.String(), nullable=True),
        sa.Column("current_latitude", sa.Numeric(10, 8), nullable=True),
        sa.Column("current_longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("last_location_update_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delay_reason", sa.String(), nullable=True),
        sa.Column("delay_minutes", sa.Integer(), nullable=True),
        sa.Column("failed_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_deliveries_driver_assignment_id", "deliveries", ["driver_assignment_id"])
    op.create_index("idx_deliveries_status", "deliveries", ["status"])
    op.create_index("idx_deliveries_pickup_code", "deliveries", ["pickup_code"])
    op.create_index("idx_deliveries_delivery_code", "deliveries", ["delivery_code"])

    # Create delivery_tracking table
    op.create_table(
        "delivery_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("delivery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("latitude", sa.Numeric(10, 8), nullable=False),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=False),
        sa.Column("accuracy_meters", sa.Numeric(10, 2), nullable=True),
        sa.Column("altitude", sa.Numeric(10, 2), nullable=True),
        sa.Column("speed_kmh", sa.Numeric(10, 2), nullable=True),
        sa.Column("heading_degrees", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", TRACKING_STATUS_ENUM, nullable=False),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("battery_level", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_delivery_tracking_driver_id", "delivery_tracking", ["driver_id"])
    op.create_index("idx_delivery_tracking_recorded_at", "delivery_tracking", ["recorded_at"])
    # Create GIST index for geospatial queries
    op.execute("CREATE INDEX idx_delivery_tracking_location ON delivery_tracking USING GIST (point(longitude, latitude))")

    # Create payment_allocations table
    op.create_table(
        "payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("transport_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("allocation_type", ALLOCATION_TYPE_ENUM, nullable=False),
        sa.Column("payer", sa.String(20), nullable=False),
        sa.Column("payee", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default='USD', nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("status", ALLOCATION_STATUS_ENUM, server_default='PENDING', nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("held_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("refund_reason", sa.String(), nullable=True),
        sa.Column("external_payment_id", sa.String(100), nullable=True),
        sa.Column("external_transaction_id", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_payment_allocations_payer", "payment_allocations", ["payer"])
    op.create_index("idx_payment_allocations_payee", "payment_allocations", ["payee"])
    op.create_index("idx_payment_allocations_status", "payment_allocations", ["status"])
    op.create_index("idx_payment_allocations_created_at", "payment_allocations", ["created_at"])

    # Create settlements table
    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("settlement_type", SETTLEMENT_TYPE_ENUM, nullable=False),
        sa.Column("gross_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("deductions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("net_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default='USD', nullable=False),
        sa.Column("goods_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("transport_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("platform_fee_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("other_deductions", sa.Numeric(15, 2), server_default='0', nullable=False),
        sa.Column("payout_method", sa.String(30), nullable=False),
        sa.Column("payout_reference", sa.String(100), nullable=True),
        sa.Column("status", SETTLEMENT_STATUS_ENUM, server_default='PENDING', nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default='0', nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_transaction_id", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_settlements_user_id", "settlements", ["user_id"])
    op.create_index("idx_settlements_status", "settlements", ["status"])
    op.create_index("idx_settlements_created_at", "settlements", ["created_at"])
    op.create_index("idx_settlements_next_retry_at", "settlements", ["next_retry_at"], postgresql_where=sa.text("status = 'FAILED'"))

    # Create disputes table
    op.create_table(
        "disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("transport_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transport_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("delivery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deliveries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("raised_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("dispute_type", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("disputed_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("currency", sa.String(3), server_default='USD', nullable=False),
        sa.Column("status", DISPUTE_STATUS_ENUM, server_default='OPEN', nullable=False),
        sa.Column("priority", sa.String(20), server_default='NORMAL', nullable=False),
        sa.Column("resolution_type", sa.String(50), nullable=True),
        sa.Column("resolution_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("resolution_notes", sa.String(), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to_admin", sa.Boolean(), server_default='false', nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_level", sa.Integer(), server_default='0', nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default='1', nullable=False),
    )
    op.create_index("idx_disputes_raised_by", "disputes", ["raised_by"])
    op.create_index("idx_disputes_status", "disputes", ["status"])
    op.create_index("idx_disputes_priority", "disputes", ["priority"])
    op.create_index("idx_disputes_created_at", "disputes", ["created_at"])
    op.create_index("idx_disputes_response_due_at", "disputes", ["response_due_at"], postgresql_where=sa.text("status = 'OPEN'"))

    # Create dispute_evidence table
    op.create_table(
        "dispute_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("dispute_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(30), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_mime_type", sa.String(100), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_dispute_evidence_uploaded_by", "dispute_evidence", ["uploaded_by"])

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("channels", postgresql.ARRAY(sa.String()), server_default=postgresql.array(['PUSH']), nullable=False),
        sa.Column("status", NOTIFICATION_STATUS_ENUM, server_default='PENDING', nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_notifications_type", "notifications", ["notification_type"])
    op.create_index("idx_notifications_status", "notifications", ["status"])
    op.create_index("idx_notifications_created_at", "notifications", ["created_at"])
    op.create_index("idx_notifications_expires_at", "notifications", ["expires_at"], postgresql_where=sa.text("expires_at IS NOT NULL"))

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_ip_address", sa.INET(), nullable=True),
        sa.Column("actor_user_agent", sa.String(), nullable=True),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("changed_fields", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("idx_audit_logs_correlation_id", "audit_logs", ["correlation_id"])

    # Create triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply triggers to tables with updated_at
    for table in ["transport_requests", "driver_assignments", "deliveries", "transport_negotiations"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ["transport_requests", "driver_assignments", "deliveries", "transport_negotiations"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    # Drop tables
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("dispute_evidence")
    op.drop_table("disputes")
    op.drop_table("settlements")
    op.drop_table("payment_allocations")
    op.drop_table("delivery_tracking")
    op.drop_table("deliveries")
    op.drop_table("driver_assignments")
    op.drop_table("negotiation_messages")
    op.drop_table("transport_negotiations")
    op.drop_table("transport_quotes")
    op.drop_table("transport_requests")

    # Drop indexes
    op.drop_index("idx_delivery_tracking_location", table_name="delivery_tracking")

    # Drop columns from orders
    op.drop_column('orders', 'transport_fee_payer')
    op.drop_column('orders', 'transport_fee')
    op.drop_column('orders', 'transport_mode')
    op.drop_column('orders', 'transport_responsible_party')

    # Drop enums
    NOTIFICATION_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    DISPUTE_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    SETTLEMENT_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    SETTLEMENT_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    ALLOCATION_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    ALLOCATION_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    TRACKING_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    DELIVERY_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    ASSIGNMENT_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    MESSAGE_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    NEGOTIATION_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    TRANSPORT_QUOTE_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    TRANSPORT_REQUEST_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    TRANSPORT_MODE_ENUM.drop(op.get_bind(), checkfirst=True)
