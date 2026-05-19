"""Pure unit tests for Dispute domain — lifecycle, status transitions, validation."""
import pytest
from uuid import uuid4

from app.domain.disputes.entities import Dispute
from app.domain.disputes.exceptions import DisputeAlreadyResolved, DisputeNotOpen, InvalidDisputeTransition
from app.domain.disputes.value_objects import DisputeStatus
from app.domain.shared_kernel.identifiers import DisputeId, OrderId, UserId


class TestDisputeStatus:
    def test_valid_transitions_from_open(self) -> None:
        status = DisputeStatus.OPEN
        assert status.can_transition_to(DisputeStatus.UNDER_REVIEW)
        assert status.can_transition_to(DisputeStatus.CLOSED)
        assert not status.can_transition_to(DisputeStatus.PROPOSED_OFFER)
        assert not status.can_transition_to(DisputeStatus.RESOLVED)
        assert not status.can_transition_to(DisputeStatus.ESCALATED)

    def test_valid_transitions_from_under_review(self) -> None:
        status = DisputeStatus.UNDER_REVIEW
        assert status.can_transition_to(DisputeStatus.PROPOSED_OFFER)
        assert status.can_transition_to(DisputeStatus.ESCALATED)
        assert status.can_transition_to(DisputeStatus.RESOLVED)
        assert not status.can_transition_to(DisputeStatus.OPEN)
        assert not status.can_transition_to(DisputeStatus.CLOSED)

    def test_valid_transitions_from_proposed_offer(self) -> None:
        status = DisputeStatus.PROPOSED_OFFER
        assert status.can_transition_to(DisputeStatus.RESOLVED)
        assert status.can_transition_to(DisputeStatus.UNDER_REVIEW)
        assert not status.can_transition_to(DisputeStatus.OPEN)
        assert not status.can_transition_to(DisputeStatus.ESCALATED)

    def test_terminal_states(self) -> None:
        assert not DisputeStatus.RESOLVED.can_transition_to(DisputeStatus.OPEN)
        assert not DisputeStatus.RESOLVED.can_transition_to(DisputeStatus.UNDER_REVIEW)
        assert not DisputeStatus.CLOSED.can_transition_to(DisputeStatus.OPEN)
        assert not DisputeStatus.CLOSED.can_transition_to(DisputeStatus.UNDER_REVIEW)


class TestDisputeCreate:
    def test_create_dispute_emits_event(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        assert dispute.status == DisputeStatus.OPEN
        events = dispute.pull_events()
        assert len(events) == 1
        assert events[0].__class__.__name__ == "DisputeCreated"


class TestDisputeAssignAgent:
    def test_assign_agent_transitions_to_under_review(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        agent_id = UserId(uuid4())
        dispute.assign_agent(agent_id)
        assert dispute.status == DisputeStatus.UNDER_REVIEW
        assert dispute.agent_assigned == agent_id

    def test_assign_agent_from_non_open_raises(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        with pytest.raises(DisputeNotOpen):
            dispute.assign_agent(UserId(uuid4()))


class TestDisputeProposeOffer:
    def test_propose_offer_from_under_review(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund for quality issue",
        )
        assert dispute.status == DisputeStatus.PROPOSED_OFFER
        assert dispute.proposed_discount == 15.0
        assert dispute.proposed_refund_amount == 150.0

    def test_propose_offer_emits_event(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund",
        )
        events = dispute.pull_events()
        assert len(events) == 2  # DisputeCreated + DisputeProposedOffer
        assert events[1].__class__.__name__ == "DisputeProposedOffer"

    def test_propose_offer_invalid_discount(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        with pytest.raises(ValueError):
            dispute.propose_offer(
                discount_percent=150.0,
                refund_amount=150.0,
                proposed_by=UserId(uuid4()),
                memo="Invalid discount",
            )

    def test_propose_offer_invalid_refund(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        with pytest.raises(ValueError):
            dispute.propose_offer(
                discount_percent=15.0,
                refund_amount=-50.0,
                proposed_by=UserId(uuid4()),
                memo="Invalid refund",
            )


class TestDisputeAcceptOffer:
    def test_buyer_accepts_offer(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund",
        )
        dispute.accept_offer(as_buyer=True)
        assert dispute.buyer_accepted is True
        assert dispute.status == DisputeStatus.PROPOSED_OFFER  # Not resolved yet

    def test_seller_accepts_offer(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund",
        )
        dispute.accept_offer(as_buyer=False)
        assert dispute.seller_accepted is True
        assert dispute.status == DisputeStatus.PROPOSED_OFFER  # Not resolved yet

    def test_both_accept_resolves_dispute(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund",
        )
        dispute.accept_offer(as_buyer=True)
        dispute.accept_offer(as_buyer=False)
        assert dispute.status == DisputeStatus.RESOLVED

    def test_reject_offer_returns_to_review(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.propose_offer(
            discount_percent=15.0,
            refund_amount=150.0,
            proposed_by=UserId(uuid4()),
            memo="Partial refund",
        )
        dispute.reject_offer()
        assert dispute.status == DisputeStatus.UNDER_REVIEW
        assert dispute.proposed_discount == 0.0
        assert dispute.proposed_refund_amount == 0.0


class TestDisputeResolve:
    def test_resolve_dispute(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.resolve(
            resolution="Full refund to buyer",
            release_to_farmer=False,
        )
        assert dispute.status == DisputeStatus.RESOLVED
        assert dispute.resolution == "Full refund to buyer"

    def test_resolve_emits_event(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.resolve(
            resolution="Full refund to buyer",
            release_to_farmer=False,
        )
        events = dispute.pull_events()
        assert len(events) == 2  # DisputeCreated + DisputeResolved
        assert events[1].__class__.__name__ == "DisputeResolved"

    def test_resolve_already_resolved_raises(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.resolve(
            resolution="Full refund to buyer",
            release_to_farmer=False,
        )
        with pytest.raises(DisputeAlreadyResolved):
            dispute.resolve(
                resolution="Another resolution",
                release_to_farmer=False,
            )


class TestDisputeEscalate:
    def test_escalate_from_under_review(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.escalate(
            escalated_by=UserId(uuid4()),
            reason="Complex case requiring legal review",
        )
        assert dispute.status == DisputeStatus.ESCALATED

    def test_escalate_emits_event(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.escalate(
            escalated_by=UserId(uuid4()),
            reason="Complex case",
        )
        events = dispute.pull_events()
        assert len(events) == 2  # DisputeCreated + DisputeEscalated
        assert events[1].__class__.__name__ == "DisputeEscalated"

    def test_escalate_from_invalid_state_raises(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        with pytest.raises(InvalidDisputeTransition):
            dispute.escalate(
                escalated_by=UserId(uuid4()),
                reason="Cannot escalate from OPEN",
            )


class TestDisputeClose:
    def test_close_from_open(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.close()
        assert dispute.status == DisputeStatus.CLOSED

    def test_close_from_escalated(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        dispute.escalate(
            escalated_by=UserId(uuid4()),
            reason="Complex case",
        )
        dispute.close()
        assert dispute.status == DisputeStatus.CLOSED

    def test_close_from_invalid_state_raises(self) -> None:
        dispute = Dispute.create(
            dispute_id=DisputeId(uuid4()),
            order_id=OrderId(uuid4()),
            raised_by=UserId(uuid4()),
            dispute_type="quality",
            description="Product quality issue",
        )
        dispute.assign_agent(UserId(uuid4()))
        with pytest.raises(InvalidDisputeTransition):
            dispute.close()
