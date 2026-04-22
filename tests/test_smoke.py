"""
Smoke tests for the core modules. Run with: pytest tests/

These are not a full test suite — they confirm that the modules load, that
the valuation model returns sensible numbers, and that the budget allocator
sums correctly. A real production codebase would add fuzzing, edge-case
coverage, and input validation tests.
"""

from src.valuation import (
    PlayerFeatures,
    Position,
    EligibilityClass,
    value_player,
)
from src.valuation.features import PortalDemandSignal, OffCourtSignal
from src.budget import ucla_2026_27_scenario
from src.roster import balanced_veteran, stars_and_scrubs, development_flywheel
from src.portal import PortalScenario, score_scenario, Decision


def test_valuation_returns_positive_value_for_elite_player():
    feat = PlayerFeatures(
        name="Test Elite",
        position=Position.PG,
        eligibility_class=EligibilityClass.SR,
        production_score=90,
        portal_demand=PortalDemandSignal(p4_offers_count=8),
        off_court=OffCourtSignal(social_following_total=400_000),
        on3_nil_valuation_usd=1_500_000,
    )
    result = value_player(feat)
    assert result.point_estimate > 1_000_000
    assert result.low_band < result.point_estimate < result.high_band
    assert result.reservation_price is not None


def test_valuation_returns_sensible_value_for_role_player():
    feat = PlayerFeatures(
        name="Test Role",
        position=Position.SG,
        eligibility_class=EligibilityClass.JR,
        production_score=55,
    )
    result = value_player(feat)
    assert 150_000 < result.point_estimate < 800_000


def test_budget_allocator_sums_correctly():
    alloc = ucla_2026_27_scenario()
    total_allocated = sum(a.dollars for a in alloc.sport_allocations)
    # Allow $1 rounding slack
    assert abs(total_allocated - alloc.rev_share_cap) <= 1


def test_ucla_mbb_gets_15_percent():
    alloc = ucla_2026_27_scenario()
    expected_mbb = int(round(alloc.rev_share_cap * 0.15))
    assert abs(alloc.mbb_rev_share - expected_mbb) <= 1


def test_archetype_shares_sum_to_one():
    for arch in [stars_and_scrubs(), balanced_veteran(), development_flywheel()]:
        assert abs(sum(arch.slot_shares) - 1.0) < 0.01, f"{arch.name} shares don't sum"


def test_portal_decision_pass_on_bad_deal():
    bad = PortalScenario(
        scenario_id="test_bad",
        player="Overpriced",
        context="test",
        our_valuation_usd=500_000,
        market_price_usd=2_500_000,
        marginal_wins=2.0,
        fit_multiplier=1.0,
        opportunity_cost_index=1.8,
    )
    result = score_scenario(bad)
    assert result.decision == Decision.PASS


def test_portal_decision_match_on_good_deal():
    good = PortalScenario(
        scenario_id="test_good",
        player="Bargain",
        context="test",
        our_valuation_usd=1_500_000,
        market_price_usd=1_000_000,
        marginal_wins=4.0,
        fit_multiplier=1.2,
        opportunity_cost_index=0.5,
    )
    result = score_scenario(good)
    assert result.decision == Decision.MATCH


if __name__ == "__main__":
    # Quick self-check if pytest isn't installed.
    test_valuation_returns_positive_value_for_elite_player()
    test_valuation_returns_sensible_value_for_role_player()
    test_budget_allocator_sums_correctly()
    test_ucla_mbb_gets_15_percent()
    test_archetype_shares_sum_to_one()
    test_portal_decision_pass_on_bad_deal()
    test_portal_decision_match_on_good_deal()
    print("All smoke tests passed.")
