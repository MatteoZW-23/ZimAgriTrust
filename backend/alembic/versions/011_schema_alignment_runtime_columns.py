from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


LOGISTICS_ENUM = postgresql.ENUM(
    "PLATFORM",
    "SELF_COLLECT",
    "SELF_DELIVER",
    "PLATFORM_FLEET",
    "COOPERATIVE",
    name="logisticstype",
)


def upgrade() -> None:
    bind = op.get_bind()
    LOGISTICS_ENUM.create(bind, checkfirst=True)

    op.add_column("offers", sa.Column("currency", sa.String(length=5), nullable=True))
    op.add_column("offers", sa.Column("logistics_type", LOGISTICS_ENUM, nullable=True))
    op.add_column("offers", sa.Column("buyer_message", sa.Text(), nullable=True))

    op.add_column("orders", sa.Column("quantity", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("currency", sa.String(length=5), nullable=True))
    op.add_column("orders", sa.Column("platform_fee", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("seller_payout", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("logistics_type", LOGISTICS_ENUM, nullable=True))
    op.add_column("orders", sa.Column("handover_code", sa.String(length=10), nullable=True))
    op.add_column("orders", sa.Column("transport_insurance_elected", sa.Boolean(), nullable=True))
    op.add_column("orders", sa.Column("transport_insurance_fee", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("refunded_amount", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("adjustment_memo", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("transport_commission", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("driver_payout", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("fraud_risk_score", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("fraud_risk_level", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("fraud_flags", sa.JSON(), nullable=True))
    op.add_column("orders", sa.Column("ai_reviewed", sa.Boolean(), nullable=True))

    op.add_column("ledger_entries", sa.Column("entry_metadata", sa.JSON(), nullable=True))

    op.add_column("system_audits", sa.Column("target_type", sa.String(length=30), nullable=True))
    op.add_column("system_audits", sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("system_audits", sa.Column("details", sa.JSON(), nullable=True))
    op.add_column("system_audits", sa.Column("note", sa.Text(), nullable=True))
    op.add_column("system_audits", sa.Column("client_ip", sa.String(length=45), nullable=True))

    op.add_column("supplier_profiles", sa.Column("subscription_plan", sa.String(length=20), nullable=True))
    op.add_column("supplier_profiles", sa.Column("subscription_status", sa.String(length=20), nullable=True))
    op.add_column("supplier_profiles", sa.Column("subscription_start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("supplier_profiles", sa.Column("subscription_end_date", sa.DateTime(timezone=True), nullable=True))

    op.add_column("agent_applications", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("agent_applications", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("agent_applications", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("agent_applications", sa.Column("next_of_kin", sa.String(length=200), nullable=True))
    op.add_column("agent_applications", sa.Column("profile_photo", sa.String(length=500), nullable=True))
    op.add_column("agent_applications", sa.Column("uploaded_documents", sa.JSON(), nullable=True))
    op.add_column("agent_applications", sa.Column("background_details", sa.String(length=2000), nullable=True))

    op.add_column("supplier_orders", sa.Column("logistics_delivery_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.add_column("notification_preferences", sa.Column("category_preferences", sa.JSON(), nullable=True))
    op.add_column(
        "notification_preferences",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.execute(sa.text(
        """
        UPDATE offers o
        SET currency = COALESCE(l.currency, 'USD'),
            logistics_type = 'PLATFORM'::logisticstype
        FROM listings l
        WHERE o.listing_id = l.id
        """
    ))

    op.execute(sa.text(
        """
        UPDATE orders o
        SET quantity = COALESCE(l.quantity, l.quantity_kg, 0),
            currency = COALESCE(ofr.currency, l.currency, 'USD'),
            platform_fee = COALESCE(o.platform_fee, 0),
            seller_payout = COALESCE(o.seller_payout, o.total_amount - COALESCE(o.platform_fee, 0)),
            logistics_type = CASE
                WHEN o.transport_mode = 'SELF_PICKUP' THEN 'SELF_COLLECT'
                WHEN o.transport_mode = 'SELF_DELIVERY' THEN 'SELF_DELIVER'
                ELSE 'PLATFORM'
            END::logisticstype,
            handover_code = COALESCE(o.handover_code, UPPER(SUBSTRING(MD5(COALESCE(o.order_number, o.id::text)), 1, 6))),
            transport_insurance_elected = COALESCE(o.transport_insurance_elected, FALSE),
            transport_insurance_fee = COALESCE(o.transport_insurance_fee, 0),
            refunded_amount = COALESCE(o.refunded_amount, 0),
            transport_commission = COALESCE(o.transport_commission, 0),
            driver_payout = COALESCE(o.driver_payout, 0),
            fraud_risk_score = COALESCE(o.fraud_risk_score, 0),
            fraud_risk_level = COALESCE(o.fraud_risk_level, 'low'),
            fraud_flags = COALESCE(o.fraud_flags, '{}'::json),
            ai_reviewed = COALESCE(o.ai_reviewed, FALSE)
        FROM listings l, offers ofr
        WHERE o.listing_id = l.id
          AND ofr.id = o.offer_id
        """
    ))

    op.alter_column("orders", "quantity", existing_type=sa.Float(), nullable=False)

    op.execute(sa.text(
        """
        UPDATE ledger_entries
        SET entry_metadata = metadata
        WHERE entry_metadata IS NULL AND metadata IS NOT NULL
        """
    ))

    op.execute(sa.text(
        """
        UPDATE system_audits
        SET target_type = entity_type,
            target_id = entity_id,
            details = changes,
            client_ip = ip_address
        WHERE target_type IS NULL
        """
    ))

    op.execute(sa.text(
        """
        UPDATE agent_applications
        SET first_name = COALESCE(first_name, split_part(full_name, ' ', 1)),
            last_name = COALESCE(
                last_name,
                CASE
                    WHEN position(' ' in full_name) > 0 THEN substring(full_name from position(' ' in full_name) + 1)
                    ELSE NULL
                END
            ),
            address = COALESCE(address, concat_ws(', ', province, district)),
            uploaded_documents = COALESCE(uploaded_documents, documents::json)
        """
    ))

    op.execute(sa.text(
        """
        UPDATE notification_preferences
        SET category_preferences = json_build_object(
            'order_updates', order_updates,
            'price_alerts', price_alerts,
            'promotional', promotional,
            'dispute_updates', dispute_updates,
            'payment_updates', payment_updates,
            'quiet_hours_start', quiet_hours_start,
            'quiet_hours_end', quiet_hours_end
        )::json,
            created_at = COALESCE(created_at, updated_at, now())
        """
    ))


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_column("notification_preferences", "created_at")
    op.drop_column("notification_preferences", "category_preferences")

    op.drop_column("supplier_orders", "logistics_delivery_id")

    op.drop_column("agent_applications", "background_details")
    op.drop_column("agent_applications", "uploaded_documents")
    op.drop_column("agent_applications", "profile_photo")
    op.drop_column("agent_applications", "next_of_kin")
    op.drop_column("agent_applications", "address")
    op.drop_column("agent_applications", "last_name")
    op.drop_column("agent_applications", "first_name")

    op.drop_column("supplier_profiles", "subscription_end_date")
    op.drop_column("supplier_profiles", "subscription_start_date")
    op.drop_column("supplier_profiles", "subscription_status")
    op.drop_column("supplier_profiles", "subscription_plan")

    op.drop_column("system_audits", "client_ip")
    op.drop_column("system_audits", "note")
    op.drop_column("system_audits", "details")
    op.drop_column("system_audits", "target_id")
    op.drop_column("system_audits", "target_type")

    op.drop_column("ledger_entries", "entry_metadata")

    op.drop_column("orders", "ai_reviewed")
    op.drop_column("orders", "fraud_flags")
    op.drop_column("orders", "fraud_risk_level")
    op.drop_column("orders", "fraud_risk_score")
    op.drop_column("orders", "driver_payout")
    op.drop_column("orders", "transport_commission")
    op.drop_column("orders", "adjustment_memo")
    op.drop_column("orders", "refunded_amount")
    op.drop_column("orders", "transport_insurance_fee")
    op.drop_column("orders", "transport_insurance_elected")
    op.drop_column("orders", "handover_code")
    op.drop_column("orders", "logistics_type")
    op.drop_column("orders", "seller_payout")
    op.drop_column("orders", "platform_fee")
    op.drop_column("orders", "currency")
    op.drop_column("orders", "quantity")

    op.drop_column("offers", "buyer_message")
    op.drop_column("offers", "logistics_type")
    op.drop_column("offers", "currency")

    LOGISTICS_ENUM.drop(bind, checkfirst=True)
