"""
Parameterized roster archetypes.

An archetype is a shape — how dollars distribute across 15 roster spots and
what the expected-wins profile looks like. The three archetypes below
correspond to the strategic discussion in docs/03_roster_archetypes.md.

Each archetype returns a list of `slot_budgets` — 15 dollar amounts that sum
to approximately the target budget. These become the "price tags" that the
roster constructor tries to fill with actual players.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Archetype(str, Enum):
    STARS_AND_SCRUBS = "stars_and_scrubs"
    BALANCED_VETERAN = "balanced_veteran"
    DEVELOPMENT_FLYWHEEL = "development_flywheel"


@dataclass
class ArchetypeProfile:
    """Full description of an archetype, including expected outcomes."""
    name: str
    archetype: Archetype
    description: str
    slot_shares: list[float]      # 15 fractions of the total budget; sum ~1.0
    exp_wins_mean: float           # projected season wins
    exp_wins_std: float            # variance
    multi_year_ev: float           # 0-1 scale: value carried forward
    injury_sensitivity: float      # 0-1 scale: higher = more fragile

    def slot_budgets(self, total_budget_usd: int) -> list[int]:
        """Apply the archetype's distribution to a specific budget."""
        return [int(round(total_budget_usd * share)) for share in self.slot_shares]


def stars_and_scrubs() -> ArchetypeProfile:
    """
    One superstar, one secondary star, role players fill the rest.
    Top-heavy. Maximum ceiling, minimum floor.
    """
    shares = [
        0.355, 0.175, 0.090, 0.075, 0.065,   # top 5: one mega + secondary + 3 starters
        0.040, 0.040, 0.040,                 # 6-8: rotation
        0.025, 0.025, 0.025,                 # 9-11: end of bench
        0.0125, 0.0125, 0.0125, 0.0125,      # 12-15: developmental
    ]  # sums to 1.000
    return ArchetypeProfile(
        name="Stars and Scrubs",
        archetype=Archetype.STARS_AND_SCRUBS,
        description=(
            "One ~$2.2M star anchors the roster; one ~$1.1M secondary. "
            "Thirteen players spread across $90K-$550K. Maximum tournament "
            "ceiling; high injury risk."
        ),
        slot_shares=shares,
        exp_wins_mean=22.0,
        exp_wins_std=4.5,
        multi_year_ev=0.20,
        injury_sensitivity=0.85,
    )


def balanced_veteran() -> ArchetypeProfile:
    """
    Three $1M+ proven vets, no mega-contract. Highest floor.
    """
    shares = [
        0.195, 0.180, 0.160, 0.090, 0.085,    # top 5: 3 vets + 2 starters
        0.050, 0.050,                          # 6-7: sixth/seventh
        0.035, 0.035, 0.035,                   # 8-10: rotation
        0.020, 0.020, 0.020,                   # 11-13: developmental
        0.0125, 0.0125,                        # 14-15: walk-on+
    ]  # sums to 1.000
    return ArchetypeProfile(
        name="Balanced Veteran",
        archetype=Archetype.BALANCED_VETERAN,
        description=(
            "Three $1.0-1.2M proven starters, no single mega-deal. "
            "High regular-season floor, moderate tournament ceiling, "
            "best suited to systems that reward veteran decision-making."
        ),
        slot_shares=shares,
        exp_wins_mean=23.5,
        exp_wins_std=2.8,
        multi_year_ev=0.35,
        injury_sensitivity=0.45,
    )


def development_flywheel() -> ArchetypeProfile:
    """
    No contract over ~$800K. Invest in upside, compound value across years.
    """
    shares = [
        0.135, 0.115, 0.105, 0.095, 0.085,   # top 5: high-upside core
        0.060, 0.060, 0.060,                  # 6-8: rotation
        0.045, 0.045, 0.045,                  # 9-11: reserves
        0.0375, 0.0375, 0.0375, 0.0375,       # 12-15: developmental
    ]  # sums to 1.000
    return ArchetypeProfile(
        name="Development Flywheel",
        archetype=Archetype.DEVELOPMENT_FLYWHEEL,
        description=(
            "No player above ~$800K; bet on internal growth and underclassmen. "
            "Lower one-year floor, highest multi-year EV. Requires patient "
            "fanbase and coaching staff with real development track record."
        ),
        slot_shares=shares,
        exp_wins_mean=19.5,
        exp_wins_std=3.5,
        multi_year_ev=0.70,
        injury_sensitivity=0.30,
    )


def all_archetypes() -> list[ArchetypeProfile]:
    return [stars_and_scrubs(), balanced_veteran(), development_flywheel()]


def compare_archetypes(total_budget_usd: int) -> None:
    """Pretty-print a comparison table across all three archetypes."""
    print()
    print("=" * 92)
    print(f"Archetype comparison at ${total_budget_usd:,} total budget")
    print("=" * 92)
    print(f"{'Archetype':<25}{'Top 3 slots':>36}{'Exp Wins':>12}{'Std Dev':>10}{'Multi-Yr':>10}")
    print("-" * 92)
    for arch in all_archetypes():
        slots = arch.slot_budgets(total_budget_usd)
        top3 = f"${slots[0]:,} / ${slots[1]:,} / ${slots[2]:,}"
        print(
            f"{arch.name:<25}"
            f"{top3:>36}"
            f"{arch.exp_wins_mean:>12.1f}"
            f"{arch.exp_wins_std:>10.1f}"
            f"{arch.multi_year_ev:>10.2f}"
        )
    print("=" * 92)
    print()


if __name__ == "__main__":
    compare_archetypes(6_200_000)
