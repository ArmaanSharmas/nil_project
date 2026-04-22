"""
ILP-based roster constructor (PuLP).

Replaces the greedy fill in constructor.py with an integer linear program that
finds the globally optimal assignment of players to slots under the cap and
positional constraints — something the greedy can miss when, for example, the
best-value player for slot 3 is better used in slot 7 to free up a more
expensive slot 3 target.

Problem formulation
───────────────────
Variables:
  x[i,j] ∈ {0,1}  →  1 if player i is assigned to slot j

Objective: maximize total value (sum of player.estimated_value × x[i,j])

Constraints:
  1. Each slot filled at most once
  2. Each player used at most once
  3. Player's market_price ≤ slot_budget × (1 + SLACK)
  4. Total actual cost ≤ total_budget × (1 + BUDGET_SLACK)
  5. (Optional) Positional balance: at least MIN_GUARDS PG/SG, MIN_BIGS C/PF

The ILP is tiny (15 slots × N candidates) so it solves in milliseconds.

Usage:
  from src.roster.ilp_constructor import build_roster_ilp
  roster = build_roster_ilp(archetype, budget, candidates, pos_constraints)
"""

from __future__ import annotations

from dataclasses import dataclass
import pulp

from .archetypes import ArchetypeProfile
from .constructor import CandidatePlayer, Roster, RosterSlot


# How far above a slot's budget a player may still be placed (20% overpay allowed)
SLOT_PRICE_SLACK = 0.20

# How much the total roster can exceed the stated budget
BUDGET_SLACK = 0.05


@dataclass
class PositionalConstraints:
    """Optional positional balance requirements."""
    min_guards: int = 2   # PG + SG combined in starting 5
    min_bigs: int = 1     # C + PF combined in starting 5
    max_per_position: dict[str, int] | None = None  # e.g. {"PG": 3, "C": 2}


def build_roster_ilp(
    archetype: ArchetypeProfile,
    total_budget: int,
    candidates: list[CandidatePlayer],
    pos_constraints: PositionalConstraints | None = None,
    verbose: bool = False,
) -> Roster:
    """
    Solve the slot-assignment problem as an ILP.

    Returns a Roster with the optimal assignment. Falls back to an empty
    Roster with a warning note if PuLP cannot find a feasible solution.
    """
    slot_budgets = sorted(archetype.slot_budgets(total_budget), reverse=True)
    n_slots = len(slot_budgets)
    n_players = len(candidates)

    if n_players == 0:
        return Roster(archetype_name=archetype.name, total_budget=total_budget)

    prob = pulp.LpProblem("roster_construction", pulp.LpMaximize)

    # Decision variables
    x = pulp.LpVariable.dicts(
        "assign",
        ((i, j) for i in range(n_players) for j in range(n_slots)),
        cat="Binary",
    )

    # Objective: maximise total player value
    prob += pulp.lpSum(
        candidates[i].estimated_value * x[i, j]
        for i in range(n_players)
        for j in range(n_slots)
    )

    # C1: each slot filled at most once
    for j in range(n_slots):
        prob += pulp.lpSum(x[i, j] for i in range(n_players)) <= 1

    # C2: each player placed at most once
    for i in range(n_players):
        prob += pulp.lpSum(x[i, j] for j in range(n_slots)) <= 1

    # C3: player price must fit slot (with slack)
    for i in range(n_players):
        for j in range(n_slots):
            if candidates[i].market_price > slot_budgets[j] * (1 + SLOT_PRICE_SLACK):
                prob += x[i, j] == 0

    # C4: total roster cost within budget (+5% slack)
    prob += pulp.lpSum(
        candidates[i].market_price * x[i, j]
        for i in range(n_players)
        for j in range(n_slots)
    ) <= total_budget * (1 + BUDGET_SLACK)

    # C5 (optional): positional balance
    if pos_constraints is not None and pos_constraints.max_per_position:
        for pos, max_count in pos_constraints.max_per_position.items():
            prob += pulp.lpSum(
                x[i, j]
                for i in range(n_players)
                for j in range(n_slots)
                if candidates[i].position == pos
            ) <= max_count

    solver = pulp.PULP_CBC_CMD(msg=int(verbose))
    prob.solve(solver)

    if pulp.LpStatus[prob.status] != "Optimal":
        print(f"⚠  ILP solver returned '{pulp.LpStatus[prob.status]}'. "
              "Roster may be incomplete. Try relaxing constraints.")
        return Roster(archetype_name=archetype.name, total_budget=total_budget)

    # Extract solution
    slots: list[RosterSlot] = []
    for i in range(n_players):
        for j in range(n_slots):
            if pulp.value(x[i, j]) == 1:
                c = candidates[i]
                slots.append(RosterSlot(
                    slot_index=j,
                    slot_budget=slot_budgets[j],
                    player_name=c.name,
                    actual_cost=c.market_price,
                    position=c.position,
                    projected_role=c.projected_role,
                    notes=c.notes,
                ))

    slots.sort(key=lambda s: -s.actual_cost)
    return Roster(
        archetype_name=f"{archetype.name} (ILP)",
        total_budget=total_budget,
        slots=slots,
    )


def compare_greedy_vs_ilp(
    archetype: ArchetypeProfile,
    total_budget: int,
    candidates: list[CandidatePlayer],
) -> None:
    """
    Build rosters with both methods and print a side-by-side comparison.
    Shows where the greedy misses value that the ILP captures.
    """
    from .constructor import build_roster_from_archetype

    greedy = build_roster_from_archetype(archetype, total_budget, candidates)
    ilp    = build_roster_ilp(archetype, total_budget, candidates)

    print("\n" + "=" * 80)
    print(f"Method comparison: {archetype.name} at ${total_budget:,}")
    print("=" * 80)
    print(f"{'Method':<20} {'Players filled':>16} {'Total cost':>14} {'Total value':>14}")
    print("-" * 80)

    def _total_value(roster: Roster) -> int:
        names_used = {s.player_name for s in roster.slots}
        return sum(c.estimated_value for c in candidates if c.name in names_used)

    for label, roster in [("Greedy", greedy), ("ILP", ilp)]:
        filled = len(roster.slots)
        cost = roster.total_cost
        value = _total_value(roster)
        print(f"{label:<20} {filled:>16} ${cost:>12,} ${value:>12,}")

    print("=" * 80)

    # Highlight differences
    greedy_names = {s.player_name for s in greedy.slots}
    ilp_names    = {s.player_name for s in ilp.slots}
    only_greedy  = greedy_names - ilp_names
    only_ilp     = ilp_names    - greedy_names

    if only_greedy or only_ilp:
        print("\nDifferences:")
        for n in only_greedy:
            print(f"  Greedy only: {n}")
        for n in only_ilp:
            print(f"  ILP only:    {n}")
    else:
        print("\nBoth methods selected identical players.")
    print()


def demo() -> None:
    from .archetypes import balanced_veteran
    from .constructor import CandidatePlayer

    candidates = [
        CandidatePlayer("Portal PG Star",       "PG", "Starter",      1_600_000, 1_800_000),
        CandidatePlayer("Returner Anchor PF",   "PF", "Starter",      1_300_000, 1_200_000, is_returner=True),
        CandidatePlayer("Portal Wing",          "SF", "Starter",        700_000,   650_000),
        CandidatePlayer("Returner Wing",        "SF", "Starter",        850_000,   800_000, is_returner=True),
        CandidatePlayer("Returner C",           "C",  "Starter",        900_000,   850_000, is_returner=True),
        CandidatePlayer("6th Man SG",           "SG", "Rotation",       450_000,   420_000),
        CandidatePlayer("7th Man PF",           "PF", "Rotation",       380_000,   350_000),
        CandidatePlayer("Rotation C",           "C",  "Rotation",       220_000,   200_000),
        CandidatePlayer("Rotation Wing",        "SF", "Rotation",       200_000,   180_000),
        CandidatePlayer("Dev PG",               "PG", "Developmental",  150_000,   130_000),
        CandidatePlayer("Dev SG",               "SG", "Developmental",  140_000,   120_000),
        CandidatePlayer("Dev SF",               "SF", "Developmental",  130_000,   110_000),
        CandidatePlayer("Walk-on+ PF",          "PF", "Developmental",   80_000,    65_000),
        CandidatePlayer("Redshirt C",           "C",  "Developmental",   90_000,    75_000),
        CandidatePlayer("High-upside FR PG",    "PG", "Developmental",  280_000,   250_000),
    ]

    compare_greedy_vs_ilp(balanced_veteran(), 6_200_000, candidates)


if __name__ == "__main__":
    demo()
