"""
Monte Carlo wrapper for the portal decision engine.

The deterministic decision_engine.py produces a single score from point
estimates. But every input has uncertainty:
  - marginal_wins:   we know it poorly (+/- 1.5 wins is realistic)
  - fit_multiplier:  judgement call (+/- 0.15)
  - opportunity_cost: depends on how the rest of the roster fills (+/- 0.3)
  - market_price:    portal markets move; asking price != clearing price (+/- 15%)

This module draws N samples from those distributions, scores each, and
returns the fraction of simulations where each decision is optimal — giving
a probability that MATCH/COUNTER/PASS is the right call.

Usage:
    result = monte_carlo_decision(scenario, n_sims=5000)
    result.print_summary()
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .decision_engine import PortalScenario, Decision, score_scenario


@dataclass
class SimulationInputs:
    """
    Uncertainty bands around each scenario input.
    All distributions are triangular: (min, mode, max).
    The 'mode' is the point estimate in PortalScenario.
    """
    wins_spread: float = 1.5        # +/- around marginal_wins
    fit_spread: float = 0.12        # +/- around fit_multiplier
    opp_cost_spread: float = 0.30   # +/- around opportunity_cost_index
    price_spread_pct: float = 0.15  # +/- % around market_price


@dataclass
class MonteCarloResult:
    scenario_id: str
    player: str
    n_sims: int

    prob_match: float
    prob_counter: float
    prob_pass: float
    modal_decision: Decision

    score_p10: float
    score_p50: float
    score_p90: float

    raw_scores: list[float] = field(default_factory=list, repr=False)

    def print_summary(self) -> None:
        print()
        print(f"Monte Carlo: {self.player} ({self.scenario_id})")
        print(f"  n_sims={self.n_sims:,}")
        print(f"  Score distribution:  P10={self.score_p10:.2f}  P50={self.score_p50:.2f}  P90={self.score_p90:.2f}")
        print(f"  Decision probs:  MATCH={self.prob_match:.1%}  COUNTER={self.prob_counter:.1%}  PASS={self.prob_pass:.1%}")
        print(f"  Modal decision:  {self.modal_decision.value}")

        if self.prob_match > 0.60:
            conf = "HIGH CONFIDENCE — match/acquire"
        elif self.prob_pass > 0.60:
            conf = "HIGH CONFIDENCE — pass"
        elif max(self.prob_match, self.prob_counter, self.prob_pass) < 0.50:
            conf = "LOW CONFIDENCE — genuinely ambiguous; need better inputs"
        else:
            conf = "MODERATE CONFIDENCE — lean toward modal decision but revisit inputs"

        print(f"  Assessment: {conf}")
        print()


def _triangular(lo: float, mode: float, hi: float) -> float:
    """Sample from a triangular distribution."""
    return random.triangular(lo, hi, mode)


def monte_carlo_decision(
    scenario: PortalScenario,
    inputs: SimulationInputs | None = None,
    n_sims: int = 5_000,
    seed: int | None = 42,
) -> MonteCarloResult:
    """
    Run N_SIMS perturbations of scenario inputs and record decision distribution.
    """
    if seed is not None:
        random.seed(seed)

    cfg = inputs or SimulationInputs()
    scores: list[float] = []
    decisions: list[Decision] = []

    for _ in range(n_sims):
        # Sample each uncertain input
        wins = _triangular(
            max(0.1, scenario.marginal_wins - cfg.wins_spread),
            scenario.marginal_wins,
            scenario.marginal_wins + cfg.wins_spread,
        )
        fit = _triangular(
            max(0.5, scenario.fit_multiplier - cfg.fit_spread),
            scenario.fit_multiplier,
            min(1.5, scenario.fit_multiplier + cfg.fit_spread),
        )
        opp = _triangular(
            max(0.0, scenario.opportunity_cost_index - cfg.opp_cost_spread),
            scenario.opportunity_cost_index,
            min(2.0, scenario.opportunity_cost_index + cfg.opp_cost_spread),
        )
        price_factor = _triangular(
            1 - cfg.price_spread_pct,
            1.0,
            1 + cfg.price_spread_pct,
        )
        price = max(50_000, scenario.market_price_usd * price_factor)

        # Build perturbed scenario and score it
        perturbed = PortalScenario(
            scenario_id=scenario.scenario_id,
            player=scenario.player,
            context=scenario.context,
            our_valuation_usd=scenario.our_valuation_usd,
            market_price_usd=int(price),
            marginal_wins=wins,
            fit_multiplier=fit,
            opportunity_cost_index=opp,
        )
        result = score_scenario(perturbed)
        scores.append(result.score)
        decisions.append(result.decision)

    # Aggregate
    n = len(scores)
    sorted_scores = sorted(scores)
    p10 = sorted_scores[int(0.10 * n)]
    p50 = sorted_scores[int(0.50 * n)]
    p90 = sorted_scores[int(0.90 * n)]

    prob_match   = decisions.count(Decision.MATCH)   / n
    prob_counter = decisions.count(Decision.COUNTER)  / n
    prob_pass    = decisions.count(Decision.PASS)     / n

    modal = max(
        [Decision.MATCH, Decision.COUNTER, Decision.PASS],
        key=lambda d: decisions.count(d),
    )

    return MonteCarloResult(
        scenario_id=scenario.scenario_id,
        player=scenario.player,
        n_sims=n,
        prob_match=prob_match,
        prob_counter=prob_counter,
        prob_pass=prob_pass,
        modal_decision=modal,
        score_p10=p10,
        score_p50=p50,
        score_p90=p90,
        raw_scores=scores,
    )


def run_all_scenarios(csv_path, n_sims: int = 5_000) -> None:
    """Load scenarios from CSV and run Monte Carlo on each."""
    from pathlib import Path
    from .decision_engine import load_scenarios

    scenarios = load_scenarios(Path(csv_path))
    print(f"\nMonte Carlo: {len(scenarios)} scenarios, {n_sims:,} sims each\n")
    for s in scenarios:
        result = monte_carlo_decision(s, n_sims=n_sims)
        result.print_summary()


def main() -> None:
    from pathlib import Path
    default = Path(__file__).resolve().parents[2] / "data" / "raw" / "portal_scenarios.csv"
    if default.exists():
        run_all_scenarios(default)
    else:
        print(f"No scenarios file found at {default}")


if __name__ == "__main__":
    main()
