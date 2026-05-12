"""Pure unit tests for Trust domain — TrustScore clamping and recompute formulas."""
import pytest

from app.domain.trust.exceptions import InvalidTrustScore, UnsupportedRole
from app.domain.trust.policies import TrustHistory, TrustWeights, recompute
from app.domain.trust.value_objects import Role, TrustScore


class TestTrustScore:
    def test_valid_score_creation(self) -> None:
        score = TrustScore(50)
        assert score.value == 50

    def test_clamp_below_zero(self) -> None:
        score = TrustScore(-10)
        assert score.value == 0

    def test_clamp_above_hundred(self) -> None:
        score = TrustScore(150)
        assert score.value == 100

    def test_boundary_values(self) -> None:
        assert TrustScore(0).value == 0
        assert TrustScore(100).value == 100
        assert TrustScore(1).value == 1
        assert TrustScore(99).value == 99


class TestRole:
    def test_role_values(self) -> None:
        assert Role.BUYER.value == "buyer"
        assert Role.FARMER.value == "farmer"
        assert Role.AGENT.value == "agent"


class TestTrustWeights:
    def test_buyer_weights(self) -> None:
        weights = TrustWeights.for_role(Role.BUYER)
        assert weights.success_weight == 5.0
        assert weights.dispute_weight == -10.0
        assert weights.failed_weight == -5.0

    def test_farmer_weights(self) -> None:
        weights = TrustWeights.for_role(Role.FARMER)
        assert weights.success_weight == 5.0
        assert weights.dispute_weight == -10.0
        assert weights.failed_weight == 0.0  # Farmers don't have failed orders

    def test_agent_weights(self) -> None:
        weights = TrustWeights.for_role(Role.AGENT)
        assert weights.success_weight == 5.0
        assert weights.dispute_weight == -10.0
        assert weights.failed_weight == 0.0

    def test_unsupported_role_raises(self) -> None:
        with pytest.raises(UnsupportedRole):
            TrustWeights.for_role(None)


class TestRecompute:
    def test_buyer_formula_no_history(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        assert score.value == 50

    def test_buyer_formula_with_success(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=10,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 50 + (10 * 5.0) = 100
        assert score.value == 100

    def test_buyer_formula_with_disputes(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=2,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 50 + (2 * -10.0) = 30
        assert score.value == 30

    def test_buyer_formula_with_failed_orders(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=0,
            failed_orders=3,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 50 + (3 * -5.0) = 35
        assert score.value == 35

    def test_buyer_formula_mixed_history(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=5,
            disputes=1,
            failed_orders=1,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 50 + (5 * 5.0) + (1 * -10.0) + (1 * -5.0) = 50 + 25 - 10 - 5 = 60
        assert score.value == 60

    def test_farmer_formula_no_history(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        assert score.value == 50

    def test_farmer_formula_with_success(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=8,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        # 50 + (8 * 5.0) = 90
        assert score.value == 90

    def test_farmer_formula_with_disputes(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=3,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        # 50 + (3 * -10.0) = 20
        assert score.value == 20

    def test_farmer_formula_with_listings(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=0,
            failed_orders=0,
            listings_count=5,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        # 50 + (5 * 2.0) = 60
        assert score.value == 60

    def test_farmer_formula_with_leakage_penalty(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=0,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=15.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        # 50 - 15.0 = 35
        assert score.value == 35

    def test_farmer_formula_complex(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=10,
            disputes=1,
            failed_orders=0,
            listings_count=3,
            leakage_penalty=5.0,
        )
        score = recompute(role=Role.FARMER, base=base, history=history)
        # 50 + (10 * 5.0) + (1 * -10.0) + (3 * 2.0) - 5.0 = 50 + 50 - 10 + 6 - 5 = 91
        assert score.value == 91

    def test_clamping_below_zero(self) -> None:
        base = 10
        history = TrustHistory(
            successful_orders=0,
            disputes=5,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 10 + (5 * -10.0) = -40 -> clamped to 0
        assert score.value == 0

    def test_clamping_above_hundred(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=20,
            disputes=0,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.BUYER, base=base, history=history)
        # 50 + (20 * 5.0) = 150 -> clamped to 100
        assert score.value == 100

    def test_agent_formula(self) -> None:
        base = 50
        history = TrustHistory(
            successful_orders=4,
            disputes=1,
            failed_orders=0,
            listings_count=0,
            leakage_penalty=0.0,
        )
        score = recompute(role=Role.AGENT, base=base, history=history)
        # 50 + (4 * 5.0) + (1 * -10.0) = 50 + 20 - 10 = 60
        assert score.value == 60
