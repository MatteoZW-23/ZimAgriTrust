"""ORM <-> Domain mappers.

Centralizing translation here keeps the domain free of SQLAlchemy and
absorbs persistence-quirks (e.g. legacy CANCELLED/REFUNDED alias).
"""
from __future__ import annotations

from app.domain.orders.entities import Order as DomainOrder
from app.domain.orders.value_objects import LogisticsType, OrderStatus
from app.domain.shared_kernel.identifiers import OrderId, UserId
from app.domain.shared_kernel.money import Currency, Money
from app.models.listing import LogisticsType as OrmLogisticsType
from app.models.transaction import Order as OrmOrder
from app.models.transaction import OrderStatus as OrmOrderStatus


# In the ORM, OrderStatus.CANCELLED is aliased to "REFUNDED" (same str
# value). The domain treats them as equivalent; we always round-trip via
# the canonical REFUNDED value.
def _orm_status_to_domain(s: OrmOrderStatus) -> OrderStatus:
    return OrderStatus(s.value)


def _domain_status_to_orm(s: OrderStatus) -> OrmOrderStatus:
    # OrmOrderStatus enum values match domain values 1:1 by string.
    return OrmOrderStatus(s.value)


def _orm_logistics_to_domain(t: OrmLogisticsType) -> LogisticsType:
    try:
        return LogisticsType(t.value if hasattr(t, "value") else str(t))
    except ValueError:
        return LogisticsType.SELF


def to_domain(row: OrmOrder) -> DomainOrder:
    currency = Currency(row.currency or "USD")
    return DomainOrder(
        id=OrderId(row.id),
        buyer_id=UserId(row.buyer_id),
        seller_id=UserId(row.seller_id),
        order_number=row.order_number,
        total_amount=Money.from_major(row.total_amount, currency),
        seller_payout=Money.from_major(row.seller_payout, currency),
        status=_orm_status_to_domain(row.status),
        logistics_type=_orm_logistics_to_domain(row.logistics_type),
        handover_code=row.handover_code,
        created_at=row.created_at,
    )


def apply_to_orm(domain: DomainOrder, row: OrmOrder) -> None:
    """Mutate the ORM row in place to reflect the domain aggregate state.

    Only writes fields the domain owns — does not touch fraud_flags,
    transport fees, etc., which belong to other bounded contexts.
    """
    row.status = _domain_status_to_orm(domain.status)
    # All other fields are immutable from the order lifecycle's perspective
    # for this use case (confirm_delivery). Add as use cases grow.
