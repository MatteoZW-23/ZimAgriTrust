"""
Composition root for the clean-architecture endpoints.

This is the ONLY place where infrastructure adapters are wired into
application use cases. Routers depend on this module via
`Depends(get_<usecase>)`; they never see ports or adapters directly.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.application.escrow import (
    RefundEscrow,
    ReleaseEscrow,
    ResolveDispute,
)
from app.application.orders import ConfirmDelivery, GetOrder
from app.application.trust import RecomputeTrustAfterSettlement
from app.application.disputes import (
    CreateDispute,
    ResolveDispute as ResolveDisputeUseCase,
    EscalateDispute,
)
from app.infrastructure.escrow import (
    FeatureFlaggedEscrowAdapter,
    LegacyPostSettlementAdapter,
)
from app.infrastructure.notifications import LoggingNotifier
from app.infrastructure.persistence.sqlalchemy import SqlAlchemyUnitOfWork
from app.infrastructure.trust import LegacyMilestoneAdapter


def get_uow(db: Session = Depends(get_db)) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(db)


def get_recompute_trust(
    db: Session = Depends(get_db),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> RecomputeTrustAfterSettlement:
    return RecomputeTrustAfterSettlement(
        history_reader=uow.trust_history,
        repository=uow.trust,
        milestone=LegacyMilestoneAdapter(db),
        notifier=LoggingNotifier(),
    )


def get_get_order(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetOrder:
    return GetOrder(uow=uow)


def get_confirm_delivery(
    db: Session = Depends(get_db),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ConfirmDelivery:
    return ConfirmDelivery(
        uow=uow,
        # Feature-flagged: ESCROW_USE_DOMAIN env switches between legacy
        # escrow_service.release_payment and the new ReleaseEscrow use case.
        escrow=FeatureFlaggedEscrowAdapter(db),
        notifier=LoggingNotifier(),
    )


def get_release_escrow(
    db: Session = Depends(get_db),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    trust_use_case: RecomputeTrustAfterSettlement = Depends(get_recompute_trust),
) -> ReleaseEscrow:
    return ReleaseEscrow(
        uow=uow,
        notifier=LoggingNotifier(),
        post_settlement=LegacyPostSettlementAdapter(db, trust_use_case=trust_use_case),
    )


def get_refund_escrow(
    db: Session = Depends(get_db),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    trust_use_case: RecomputeTrustAfterSettlement = Depends(get_recompute_trust),
) -> RefundEscrow:
    return RefundEscrow(
        uow=uow,
        notifier=LoggingNotifier(),
        post_settlement=LegacyPostSettlementAdapter(db, trust_use_case=trust_use_case),
    )


def get_resolve_dispute(
    db: Session = Depends(get_db),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    trust_use_case: RecomputeTrustAfterSettlement = Depends(get_recompute_trust),
) -> ResolveDispute:
    return ResolveDispute(
        uow=uow,
        notifier=LoggingNotifier(),
    )


def get_create_dispute(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreateDispute:
    return CreateDispute(
        repository=uow.disputes,
        reader=uow.dispute_reader,
        notifier=LoggingNotifier(),
    )


def get_resolve_dispute_use_case(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> ResolveDisputeUseCase:
    return ResolveDisputeUseCase(
        repository=uow.disputes,
        notifier=LoggingNotifier(),
    )


def get_escalate_dispute(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> EscalateDispute:
    return EscalateDispute(
        repository=uow.disputes,
        notifier=LoggingNotifier(),
    )
    return ResolveDispute(
        uow=uow,
        notifier=LoggingNotifier(),
        post_settlement=LegacyPostSettlementAdapter(db, trust_use_case=trust_use_case),
    )
