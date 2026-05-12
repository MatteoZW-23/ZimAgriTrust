"""SQLAlchemy adapter for DisputeRepository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.disputes import DisputeRepository
from app.domain.disputes.entities import Dispute
from app.domain.disputes.value_objects import DisputeStatus
from app.domain.shared_kernel.identifiers import DisputeId, OrderId, UserId
from app.models.dispute import Dispute as OrmDispute


class SqlAlchemyDisputeRepository(DisputeRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, dispute: Dispute) -> None:
        row = self._session.get(OrmDispute, dispute.id.value)
        if row is None:
            # Create new
            row = OrmDispute(
                id=dispute.id.value,
                order_id=dispute.order_id.value,
                raised_by=dispute.raised_by.value,
                type=dispute.dispute_type,
                description=dispute.description,
                status=self._to_orm_status(dispute.status),
                agent_assigned=dispute.agent_assigned.value if dispute.agent_assigned else None,
                resolution=dispute.resolution,
                proposed_discount=dispute.proposed_discount,
                proposed_refund_amount=dispute.proposed_refund_amount,
                buyer_accepted=dispute.buyer_accepted,
                seller_accepted=dispute.seller_accepted,
                agent_resolution_memo=dispute.agent_resolution_memo,
                created_at=dispute.created_at,
            )
            self._session.add(row)
        else:
            # Update existing
            row.status = self._to_orm_status(dispute.status)
            row.agent_assigned = dispute.agent_assigned.value if dispute.agent_assigned else None
            row.resolution = dispute.resolution
            row.proposed_discount = dispute.proposed_discount
            row.proposed_refund_amount = dispute.proposed_refund_amount
            row.buyer_accepted = dispute.buyer_accepted
            row.seller_accepted = dispute.seller_accepted
            row.agent_resolution_memo = dispute.agent_resolution_memo
            self._session.add(row)

    def get_by_id(self, dispute_id: DisputeId) -> Dispute | None:
        row = self._session.get(OrmDispute, dispute_id.value)
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_order(self, order_id: OrderId) -> Dispute | None:
        row = self._session.query(OrmDispute).filter(
            OrmDispute.order_id == order_id.value
        ).first()
        if row is None:
            return None
        return self._to_domain(row)

    def _to_domain(self, row: OrmDispute) -> Dispute:
        return Dispute(
            id=DisputeId(row.id),
            order_id=OrderId(row.order_id),
            raised_by=UserId(row.raised_by),
            dispute_type=row.type,
            description=row.description,
            status=self._from_orm_status(row.status),
            agent_assigned=UserId(row.agent_assigned) if row.agent_assigned else None,
            resolution=row.resolution,
            proposed_discount=row.proposed_discount or 0.0,
            proposed_refund_amount=row.proposed_refund_amount or 0.0,
            buyer_accepted=row.buyer_accepted,
            seller_accepted=row.seller_accepted,
            agent_resolution_memo=row.agent_resolution_memo,
            created_at=row.created_at,
        )

    def _to_orm_status(self, status: DisputeStatus) -> app.models.dispute.DisputeStatus:
        mapping = {
            DisputeStatus.OPEN: app.models.dispute.DisputeStatus.OPEN,
            DisputeStatus.UNDER_REVIEW: app.models.dispute.DisputeStatus.UNDER_REVIEW,
            DisputeStatus.PROPOSED_OFFER: app.models.dispute.DisputeStatus.PROPOSED_OFFER,
            DisputeStatus.RESOLVED: app.models.dispute.DisputeStatus.RESOLVED,
            DisputeStatus.ESCALATED: app.models.dispute.DisputeStatus.ESCALATED,
            DisputeStatus.CLOSED: app.models.dispute.DisputeStatus.CLOSED,
        }
        return mapping[status]

    def _from_orm_status(self, status: app.models.dispute.DisputeStatus) -> DisputeStatus:
        mapping = {
            app.models.dispute.DisputeStatus.OPEN: DisputeStatus.OPEN,
            app.models.dispute.DisputeStatus.UNDER_REVIEW: DisputeStatus.UNDER_REVIEW,
            app.models.dispute.DisputeStatus.PROPOSED_OFFER: DisputeStatus.PROPOSED_OFFER,
            app.models.dispute.DisputeStatus.RESOLVED: DisputeStatus.RESOLVED,
            app.models.dispute.DisputeStatus.ESCALATED: DisputeStatus.ESCALATED,
            app.models.dispute.DisputeStatus.CLOSED: DisputeStatus.CLOSED,
        }
        return mapping[status]
