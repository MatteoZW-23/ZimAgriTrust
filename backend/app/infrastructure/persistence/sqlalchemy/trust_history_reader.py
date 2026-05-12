"""SQLAlchemy adapter for TrustHistoryReader — runs the COUNT queries from legacy trust_service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.trust import TrustHistoryReader
from app.domain.shared_kernel.identifiers import UserId
from app.domain.trust.policies import TrustHistory
from app.domain.trust.value_objects import Role
from app.models.dispute import Dispute
from app.models.listing import Listing
from app.models.transaction import Order, OrderStatus
from app.models.user import User as OrmUser, UserRole


def _to_domain_role(r: UserRole) -> Role | None:
    """Map ORM UserRole to domain Role. None for non-scored roles."""
    mapping = {
        UserRole.BUYER: Role.BUYER,
        UserRole.FARMER: Role.FARMER,
        UserRole.AGENT: Role.AGENT,
    }
    return mapping.get(r)


class SqlAlchemyTrustHistoryReader(TrustHistoryReader):
    def __init__(self, session: Session) -> None:
        self._session = session

    def read(self, user_id: UserId, role: Role) -> TrustHistory:
        """Execute the COUNT queries mirroring trust_service.recompute_user_scores / update_farmer_scores."""
        successful_orders = (
            self._session.query(Order)
            .filter(
                (Order.buyer_id == user_id.value) if role == Role.BUYER else (Order.seller_id == user_id.value),
                Order.status == OrderStatus.COMPLETED,
            )
            .count()
        )

        disputes = (
            self._session.query(Dispute)
            .join(Order, Dispute.order_id == Order.id)
            .filter(
                (Order.buyer_id == user_id.value) if role == Role.BUYER else (Order.seller_id == user_id.value),
            )
            .count()
        )

        failed_orders = (
            self._session.query(Order)
            .filter(
                Order.buyer_id == user_id.value,
                Order.status == OrderStatus.REFUNDED,
            )
            .count()
        ) if role == Role.BUYER else 0

        listings_count = (
            self._session.query(Listing)
            .filter(Listing.seller_id == user_id.value)
            .count()
        ) if role == Role.FARMER else 0

        # Leakage penalty — delegate to legacy function for parity.
        from app.services.trust_service import detect_leakage_risk
        user = self._session.get(OrmUser, user_id.value)
        leakage_penalty = detect_leakage_risk(self._session, user) if user else 0.0

        return TrustHistory(
            successful_orders=successful_orders,
            disputes=disputes,
            failed_orders=failed_orders,
            listings_count=listings_count,
            leakage_penalty=leakage_penalty,
        )

    def base_score(self, user_id: UserId) -> int:
        """Verification-derived base score via verification_service.get_initial_trust."""
        from app.services.verification_service import verification_service
        user = self._session.get(OrmUser, user_id.value)
        if not user:
            raise LookupError(f"User {user_id} not found")
        return verification_service.get_initial_trust(user)

    def role_of(self, user_id: UserId) -> Role | None:
        user = self._session.get(OrmUser, user_id.value)
        if not user:
            return None
        return _to_domain_role(user.role)

    def completed_count(self, user_id: UserId, *, as_buyer: bool) -> int:
        return (
            self._session.query(Order)
            .filter(
                (Order.buyer_id == user_id.value) if as_buyer else (Order.seller_id == user_id.value),
                Order.status == OrderStatus.COMPLETED,
            )
            .count()
        )
