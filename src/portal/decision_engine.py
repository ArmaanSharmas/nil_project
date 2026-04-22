"""
Portal decision engine.

Framework from docs/04_portal_scenarios.md:

    decision_score = (expected_marginal_wins * fit_multiplier) / cost_in_millions
                     - opportunity_cost_index

    decision_score > 2.0    → MATCH (or acquire)
    decision_score > 0.8    → COUNTER / NEGOTIATE
    decision_score <= 0.8   → PASS

Each input has a confidence interval in reality. This implementation returns
point-estimate scores; a future version would Monte Carlo the inputs and
report the probability that each decision is optimal. For now, the point
estimate is explicit and auditable.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Decision(str, Enum):
    MATCH = "MATCH"
    COUNTER = "COUNTER"
    PASS = "PASS"


@dataclass
class PortalScenario:
    """The inputs to a single portal decision."""
    scenario_id: str
    player: str
    context: str
    our_valuation_usd: int        # from src/valuation/model.py
    market_price_usd: int         # what it'd actually take to land/retain
    marginal_wins: float          # wins above replacement-tier alternative
    fit_multiplier: float         # 0.7-1.3; positional/system/culture fit
    opportunity_cost_index: float # 0-2; how much elsewhere suffers

    @property
    def overpay_ratio(self) -> float:
        """How far above our valuation is the market price? 1.0 = at value."""
        return self.market_price_usd / max(self.our_valuation_usd, 1)


@dataclass
class DecisionResult:
    scenario: PortalScenario
    score: float
    decision: Decision
    rationale: str

    def print_summary(self) -> None:
        s = self.scenario
        print()
        print("-" * 80)
        print(f"Scenario: {s.scenario_id}")
        print(f"Player:   {s.player}")
        print(f"Context:  {s.context}")
        print("-" * 80)
        print(f"  Our valuation:            ${s.our_valuation_usd:>12,}")
        print(f"  Market price:             ${s.market_price_usd:>12,}  "
              f"({s.overpay_ratio:.2f}x of valuation)")
        print(f"  Marginal wins:            {s.marginal_wins:>13.2f}")
        print(f"  Fit multiplier:           {s.fit_multiplier:>13.2f}")
        print(f"  Opportunity cost:         {s.opportunity_cost_index:>13.2f}")
        print(f"  → Decision score:         {self.score:>13.2f}")
        print(f"  → DECISION:               {self.decision.value}")
        print(f"  Rationale: {self.rationale}")
        print()


def score_scenario(scenario: PortalScenario) -> DecisionResult:
    """Apply the decision framework to a scenario."""
    cost_millions = scenario.market_price_usd / 1_000_000
    if cost_millions <= 0:
        raise ValueError(f"Invalid cost for scenario {scenario.scenario_id}")

    score = (
        (scenario.marginal_wins * scenario.fit_multiplier) / cost_millions
        - scenario.opportunity_cost_index
    )

    if score > 2.0:
        decision = Decision.MATCH
        rationale = (
            "Strong value per dollar even after opportunity cost. "
            "Green light to match/acquire at or near market."
        )
    elif score > 0.8:
        decision = Decision.COUNTER
        rationale = (
            "Positive but not slam-dunk. Try to counter below market — "
            "small overpays are okay, large ones are not. "
            f"Market at {scenario.overpay_ratio:.2f}x valuation."
        )
    else:
        decision = Decision.PASS
        rationale = (
            "Below threshold. Marginal wins don't justify cost once "
            "opportunity cost is netted. Reallocate to depth or different target."
        )

    # Qualifier: flag extreme overpays regardless of score.
    if scenario.overpay_ratio > 1.5 and decision == Decision.MATCH:
        rationale += (
            " ⚠ Note: market is >1.5x our valuation. Revisit inputs — either "
            "the valuation is too low or the marginal wins projection is too high."
        )

    return DecisionResult(
        scenario=scenario,
        score=round(score, 2),
        decision=decision,
        rationale=rationale,
    )


def load_scenarios(csv_path: Path) -> list[PortalScenario]:
    """Load scenarios from a CSV (see data/raw/portal_scenarios.csv for schema)."""
    scenarios: list[PortalScenario] = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenarios.append(
                PortalScenario(
                    scenario_id=row["scenario_id"],
                    player=row["player"],
                    context=row["context"],
                    our_valuation_usd=int(row["our_valuation_usd"]),
                    market_price_usd=int(row["market_price_usd"]),
                    marginal_wins=float(row["marginal_wins"]),
                    fit_multiplier=float(row["fit_multiplier"]),
                    opportunity_cost_index=float(row["opportunity_cost_index"]),
                )
            )
    return scenarios


def main() -> None:
    """Run all scenarios in the default CSV."""
    default_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "portal_scenarios.csv"
    if not default_path.exists():
        print(f"No scenarios file at {default_path}")
        return

    scenarios = load_scenarios(default_path)
    print(f"\nEvaluating {len(scenarios)} portal scenarios from {default_path.name}")
    for s in scenarios:
        result = score_scenario(s)
        result.print_summary()


if __name__ == "__main__":
    main()
