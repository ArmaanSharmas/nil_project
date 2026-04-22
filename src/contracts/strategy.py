"""
Contract type strategy engine — incentive structures, multi-year deal analysis,
and strategic recommendations for NIL roster construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

DISCOUNT_RATE = 0.08  # opportunity cost rate for NPV


class PlayerTier(Enum):
    STAR = "Star"
    SOLID_STARTER = "Solid Starter"
    ROTATION = "Rotation"
    DEVELOPMENTAL = "Developmental"


# Annual probability that a player departs (NBA, bigger offer, transfer)
DEPARTURE_PROB: dict[str, float] = {
    "Star":          0.45,
    "Solid Starter": 0.28,
    "Rotation":      0.18,
    "Developmental": 0.12,
}

# Expected marginal wins contributed per year by tier
WINS_BY_TIER: dict[str, float] = {
    "Star":          4.5,
    "Solid Starter": 2.8,
    "Rotation":      1.4,
    "Developmental": 0.6,
}

# Strategic recommendation matrix: (tier_label, contract_years) -> (label, rationale)
STRATEGY_MATRIX: dict[tuple[str, int], tuple[str, str]] = {
    ("Star", 1): (
        "Good",
        "Stars carry 40–45% annual departure risk (NBA, bigger offers). "
        "Short contracts protect cap flexibility and prevent a $4–6M/yr anchor if they leave.",
    ),
    ("Star", 2): (
        "Situational",
        "Works when the player's NBA trajectory is confirmed 2+ years out. "
        "Adds retention security but limits future reallocation if the market shifts.",
    ),
    ("Star", 3): (
        "Avoid",
        "Three-year commitments to stars risk locking up $5–18M in guaranteed money "
        "for a player who may go pro in Year 1. The wins upside rarely compensates.",
    ),
    ("Solid Starter", 1): (
        "Good",
        "Maintains cap flexibility but exposes you to open-market competition in Year 2. "
        "Best when the portal is deep at this position and replacement options are strong.",
    ),
    ("Solid Starter", 2): (
        "Ideal",
        "The sweet spot for mid-tier talent. Locks in a known contributor below Year-2 "
        "open-market rates while duration keeps cap exposure manageable. "
        "Creates roster continuity without overcommitting.",
    ),
    ("Solid Starter", 3): (
        "Situational",
        "Makes sense when eligibility allows and system fit is proven. "
        "Ensures 3-year identity continuity but limits the ability to upgrade "
        "if a better option enters the portal.",
    ),
    ("Rotation", 1): (
        "Situational",
        "Low cap risk but leaves the slot vulnerable to raiding once they show promise. "
        "Good bridge while developmental players mature behind them.",
    ),
    ("Rotation", 2): (
        "Good",
        "Depth stability at low AAV. Rotation players rarely outpace their salary "
        "within 2 years, so cap exposure stays limited even if they plateau.",
    ),
    ("Rotation", 3): (
        "Avoid",
        "Three years at rotation-level production locks up a slot and budget. "
        "Eliminates the flexibility to upgrade or reload through the portal mid-cycle.",
    ),
    ("Developmental", 1): (
        "Situational",
        "Leaves developmental players poachable once they show real improvement. "
        "Acceptable only when budget constraints are severe.",
    ),
    ("Developmental", 2): (
        "Good",
        "Locks in raw talent before they break out. If 50%+ develop into rotation "
        "contributors, the NPV of a pre-breakout deal beats annual re-signing at inflated prices.",
    ),
    ("Developmental", 3): (
        "Ideal",
        "The Flywheel strategy. Lock in at $90–150K/yr. If even 40% develop into starters, "
        "the ROI dramatically beats market-rate re-signing after Year 1. "
        "Low AAV means the downside risk is minimal even for players who don't develop.",
    ),
}


@dataclass
class IncentiveTrigger:
    name: str
    bonus_usd: int
    hit_probability: float  # 0.0 – 1.0


@dataclass
class ContractScenario:
    player_tier: str       # matches PlayerTier.value
    contract_years: int    # 1, 2, or 3
    base_salary_yr1: int
    escalator_pct: float = 0.0  # e.g. 0.08 = 8% per year
    incentive_triggers: list[IncentiveTrigger] = field(default_factory=list)


@dataclass
class YearBreakdown:
    year: int
    salary: int
    p_retention: float      # probability player is still on roster
    risk_adjusted_cost: int # salary * p_retention
    discounted_cost: int    # salary / (1+r)^year


@dataclass
class ContractAnalysis:
    years: int
    guaranteed_total: int
    incentive_ev: int
    expected_total_cost: int
    npv: int                # discounted guaranteed payments
    risk_adjusted_npv: int  # discounted risk-adjusted payments
    expected_wins: float
    cap_efficiency: float   # wins per $1M (risk-adjusted)
    year_breakdowns: list[YearBreakdown]
    recommendation: str     # Ideal / Good / Situational / Avoid
    rationale: str


def analyze_contract(scenario: ContractScenario) -> ContractAnalysis:
    tier = scenario.player_tier
    dep_prob = DEPARTURE_PROB.get(tier, 0.20)
    wins_per_year = WINS_BY_TIER.get(tier, 1.0)

    breakdowns: list[YearBreakdown] = []
    p_retention = 1.0
    for y in range(1, scenario.contract_years + 1):
        salary = int(scenario.base_salary_yr1 * (1 + scenario.escalator_pct) ** (y - 1))
        disc = (1 + DISCOUNT_RATE) ** y
        breakdowns.append(YearBreakdown(
            year=y,
            salary=salary,
            p_retention=round(p_retention, 4),
            risk_adjusted_cost=int(salary * p_retention),
            discounted_cost=int(salary / disc),
        ))
        p_retention *= (1 - dep_prob)

    guaranteed_total = sum(b.salary for b in breakdowns)
    incentive_ev = sum(int(t.hit_probability * t.bonus_usd) for t in scenario.incentive_triggers)
    expected_total_cost = guaranteed_total + incentive_ev
    npv = sum(b.discounted_cost for b in breakdowns)
    risk_adjusted_npv = sum(
        int(b.risk_adjusted_cost / (1 + DISCOUNT_RATE) ** b.year)
        for b in breakdowns
    )

    p_ret = 1.0
    expected_wins = 0.0
    for _ in range(scenario.contract_years):
        expected_wins += wins_per_year * p_ret
        p_ret *= (1 - dep_prob)

    cap_efficiency = (
        expected_wins / (risk_adjusted_npv / 1_000_000)
        if risk_adjusted_npv > 0 else 0.0
    )

    rec, rationale = STRATEGY_MATRIX.get(
        (tier, scenario.contract_years),
        ("Situational", "Evaluate based on specific player circumstances."),
    )

    return ContractAnalysis(
        years=scenario.contract_years,
        guaranteed_total=guaranteed_total,
        incentive_ev=incentive_ev,
        expected_total_cost=expected_total_cost,
        npv=npv,
        risk_adjusted_npv=risk_adjusted_npv,
        expected_wins=round(expected_wins, 1),
        cap_efficiency=round(cap_efficiency, 2),
        year_breakdowns=breakdowns,
        recommendation=rec,
        rationale=rationale,
    )


def comparison_analysis(
    tier: str,
    base_salary_yr1: int,
    escalator_pct: float = 0.08,
) -> list[ContractAnalysis]:
    """Return 1-yr, 2-yr, 3-yr analyses for side-by-side comparison."""
    return [
        analyze_contract(ContractScenario(
            player_tier=tier,
            contract_years=y,
            base_salary_yr1=base_salary_yr1,
            escalator_pct=escalator_pct,
        ))
        for y in [1, 2, 3]
    ]
