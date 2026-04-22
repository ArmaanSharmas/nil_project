"""
Cap-constrained roster construction.

Given an archetype and a candidate player pool, assign players to slots such
that the total cost stays within budget and positional needs are met.

The current implementation is greedy — it sorts candidates by value-per-dollar
and fills slots from most valuable to least. This is pragmatic and interpretable.
A more sophisticated version would solve this as an integer program, but that's
overkill for a 15-slot problem and would hide the logic behind an opaque solver.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .archetypes import ArchetypeProfile


@dataclass
class RosterSlot:
    """One filled roster spot."""
    slot_index: int              # 0-14
    slot_budget: int             # target dollars for this spot
    player_name: str
    actual_cost: int             # what the player actually costs
    position: str
    projected_role: str
    notes: str = ""

    @property
    def variance_from_slot(self) -> int:
        """Positive = paid above slot target; negative = bargain."""
        return self.actual_cost - self.slot_budget


@dataclass
class Roster:
    """A complete 15-player roster under a budget cap."""
    archetype_name: str
    total_budget: int
    slots: list[RosterSlot] = field(default_factory=list)
    unfilled_budget: int = 0

    @property
    def total_cost(self) -> int:
        return sum(s.actual_cost for s in self.slots)

    @property
    def over_budget_by(self) -> int:
        return max(0, self.total_cost - self.total_budget)

    @property
    def under_budget_by(self) -> int:
        return max(0, self.total_budget - self.total_cost)

    def print_summary(self) -> None:
        print()
        print("=" * 96)
        print(f"Roster: {self.archetype_name}  (budget: ${self.total_budget:,})")
        print("=" * 96)
        print(f"{'#':>3}  {'Slot $':>11}  {'Player':<30}  {'Pos':<4}  {'Actual $':>11}  {'Role'}")
        print("-" * 96)
        for s in sorted(self.slots, key=lambda x: -x.actual_cost):
            print(
                f"{s.slot_index + 1:>3}  "
                f"${s.slot_budget:>9,}  "
                f"{s.player_name:<30}  "
                f"{s.position:<4}  "
                f"${s.actual_cost:>9,}  "
                f"{s.projected_role}"
            )
        print("-" * 96)
        print(f"{'':>3}  {'Total:':>11}  {'':<30}  {'':<4}  ${self.total_cost:>9,}")
        if self.over_budget_by:
            print(f"⚠  Over budget by ${self.over_budget_by:,}")
        elif self.under_budget_by:
            print(f"✓  Under budget by ${self.under_budget_by:,}")
        print("=" * 96)
        print()


@dataclass
class CandidatePlayer:
    """A player eligible for consideration."""
    name: str
    position: str
    projected_role: str           # "Starter", "Rotation", "Bench", "Developmental"
    estimated_value: int          # from the valuation model
    market_price: int             # what it'd actually cost to sign/retain
    is_returner: bool = False
    notes: str = ""

    @property
    def value_per_dollar(self) -> float:
        """Higher = better bargain. Used for greedy sort."""
        return self.estimated_value / max(self.market_price, 1)


def build_roster_from_archetype(
    archetype: ArchetypeProfile,
    total_budget: int,
    candidates: list[CandidatePlayer],
) -> Roster:
    """
    Greedy roster builder.

    1. Compute slot budgets from the archetype.
    2. Sort candidates by value-per-dollar (descending).
    3. Walk down slots (largest to smallest) and match each to the highest-
       value candidate whose market_price fits within ~120% of the slot budget.
    4. If no match, leave slot open and note unfilled budget.
    """
    slot_budgets = sorted(archetype.slot_budgets(total_budget), reverse=True)
    remaining = sorted(candidates, key=lambda c: -c.value_per_dollar)
    used: set[str] = set()
    slots: list[RosterSlot] = []

    for slot_idx, slot_budget in enumerate(slot_budgets):
        pick = _select_best_fit(remaining, slot_budget, used)
        if pick is None:
            continue
        used.add(pick.name)
        slots.append(
            RosterSlot(
                slot_index=slot_idx,
                slot_budget=slot_budget,
                player_name=pick.name,
                actual_cost=pick.market_price,
                position=pick.position,
                projected_role=pick.projected_role,
                notes=pick.notes,
            )
        )

    total_spent = sum(s.actual_cost for s in slots)
    unfilled = total_budget - total_spent

    return Roster(
        archetype_name=archetype.name,
        total_budget=total_budget,
        slots=slots,
        unfilled_budget=unfilled,
    )


def _select_best_fit(
    candidates: list[CandidatePlayer],
    slot_budget: int,
    used: set[str],
) -> CandidatePlayer | None:
    """
    Find the highest-value candidate whose market price fits the slot.

    Tolerance: slot budget × 0.7 (floor) to × 1.3 (ceiling). This lets a
    slightly over-budget star fit a smaller slot at a slight overpay, or a
    cheaper role player fit a richer slot (which the constructor should
    generally avoid — if this happens often, the archetype shape is wrong).
    """
    floor = int(slot_budget * 0.7)
    ceiling = int(slot_budget * 1.3)
    best: CandidatePlayer | None = None

    for c in candidates:
        if c.name in used:
            continue
        if not (floor <= c.market_price <= ceiling):
            continue
        if best is None or c.estimated_value > best.estimated_value:
            best = c

    return best


def demo() -> None:
    """Illustrative roster build on synthetic candidates."""
    from .archetypes import balanced_veteran

    candidates = [
        CandidatePlayer("Returner A", "PF", "Starter", 1_300_000, 1_200_000, is_returner=True),
        CandidatePlayer("Portal Star Guard", "PG", "Starter", 1_200_000, 1_300_000),
        CandidatePlayer("Returner B", "SF", "Starter", 900_000, 850_000, is_returner=True),
        CandidatePlayer("Returner C", "C", "Starter", 950_000, 900_000, is_returner=True),
        CandidatePlayer("Portal Wing", "SF", "Starter", 600_000, 550_000),
        CandidatePlayer("Portal Shooter", "SG", "Starter", 550_000, 500_000),
        CandidatePlayer("Sixth Man", "SG", "Rotation", 350_000, 320_000),
        CandidatePlayer("7th Man", "PF", "Rotation", 300_000, 280_000),
        CandidatePlayer("Rotation Big", "C", "Rotation", 200_000, 180_000),
        CandidatePlayer("Rotation Wing", "SF", "Rotation", 180_000, 160_000),
        CandidatePlayer("Developmental PG", "PG", "Developmental", 140_000, 120_000),
        CandidatePlayer("Developmental SG", "SG", "Developmental", 140_000, 120_000),
        CandidatePlayer("Developmental SF", "SF", "Developmental", 130_000, 110_000),
        CandidatePlayer("Walk-on+", "PF", "Developmental", 80_000, 60_000),
        CandidatePlayer("Redshirt", "C", "Developmental", 90_000, 70_000),
    ]

    archetype = balanced_veteran()
    roster = build_roster_from_archetype(archetype, 6_200_000, candidates)
    roster.print_summary()


if __name__ == "__main__":
    demo()
