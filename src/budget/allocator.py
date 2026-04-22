"""
Top-down budget allocator.

Walks from the House settlement rev-share cap through the allocation formula
down to a Men's Basketball operating budget, combining rev-share and an
estimated third-party NIL layer.

The intent is to make every assumption explicit and tweakable. If you want to
model Kentucky's 25-30% MBB allocation instead of UCLA's 15%, change one number.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SportAllocation:
    """One sport's share of the rev-share pie."""
    sport: str
    share: float           # fraction of total rev-share (e.g., 0.15)
    dollars: int = 0       # populated by allocator

    @property
    def share_pct(self) -> str:
        return f"{self.share * 100:.1f}%"


@dataclass
class BudgetAllocation:
    """Full allocation breakdown with MBB total operating budget."""
    year: str
    rev_share_cap: int
    sport_allocations: list[SportAllocation]
    mbb_third_party_nil_low: int
    mbb_third_party_nil_base: int
    mbb_third_party_nil_high: int
    assumptions: list[str] = field(default_factory=list)

    @property
    def mbb_rev_share(self) -> int:
        for a in self.sport_allocations:
            if a.sport.lower() in {"men's basketball", "mbb", "men's bball"}:
                return a.dollars
        raise ValueError("MBB allocation not found")

    @property
    def mbb_total_low(self) -> int:
        return self.mbb_rev_share + self.mbb_third_party_nil_low

    @property
    def mbb_total_base(self) -> int:
        return self.mbb_rev_share + self.mbb_third_party_nil_base

    @property
    def mbb_total_high(self) -> int:
        return self.mbb_rev_share + self.mbb_third_party_nil_high

    def print_summary(self) -> None:
        print()
        print("=" * 72)
        print(f"Budget allocation: {self.year}")
        print("=" * 72)
        print(f"Rev-share cap (full):           ${self.rev_share_cap:>14,}")
        print("-" * 72)
        print(f"{'Sport':<25}{'Share':>10}{'Dollars':>20}")
        print("-" * 72)
        for a in self.sport_allocations:
            print(f"{a.sport:<25}{a.share_pct:>10}{'$' + format(a.dollars, ','):>20}")
        total = sum(a.dollars for a in self.sport_allocations)
        print("-" * 72)
        print(f"{'Total':<25}{'100.0%':>10}{'$' + format(total, ','):>20}")
        print()
        print(f"MBB rev-share allocation:       ${self.mbb_rev_share:>14,}")
        print(f"Third-party NIL (low):          ${self.mbb_third_party_nil_low:>14,}")
        print(f"Third-party NIL (base case):    ${self.mbb_third_party_nil_base:>14,}")
        print(f"Third-party NIL (high):         ${self.mbb_third_party_nil_high:>14,}")
        print("-" * 72)
        print(f"MBB total budget (low):         ${self.mbb_total_low:>14,}")
        print(f"MBB total budget (base):        ${self.mbb_total_base:>14,}  ← base case")
        print(f"MBB total budget (high):        ${self.mbb_total_high:>14,}")
        print("=" * 72)
        if self.assumptions:
            print("\nAssumptions:")
            for i, a in enumerate(self.assumptions, 1):
                print(f"  {i}. {a}")
        print()


def allocate_budget(
    year: str,
    rev_share_cap: int,
    sport_shares: dict[str, float],
    mbb_nil_low: int,
    mbb_nil_base: int,
    mbb_nil_high: int,
    assumptions: list[str] | None = None,
) -> BudgetAllocation:
    """
    Compute the full allocation given inputs.

    `sport_shares` must sum to ~1.0 (tolerance ±0.005). MBB allocation must be
    present under one of: "Men's Basketball", "MBB", "Men's BBall" (any case).
    """
    total_share = sum(sport_shares.values())
    if not (0.995 <= total_share <= 1.005):
        raise ValueError(
            f"Sport shares must sum to 1.0 (got {total_share:.4f}). "
            f"Shares: {sport_shares}"
        )

    sport_allocations = [
        SportAllocation(
            sport=sport,
            share=share,
            dollars=int(round(rev_share_cap * share)),
        )
        for sport, share in sport_shares.items()
    ]

    return BudgetAllocation(
        year=year,
        rev_share_cap=rev_share_cap,
        sport_allocations=sport_allocations,
        mbb_third_party_nil_low=mbb_nil_low,
        mbb_third_party_nil_base=mbb_nil_base,
        mbb_third_party_nil_high=mbb_nil_high,
        assumptions=assumptions or [],
    )


def ucla_2026_27_scenario() -> BudgetAllocation:
    """
    UCLA's projected 2026-27 MBB operating budget.

    Sourced from public reporting — see docs/01_budget_allocation.md for the
    full citation chain. Every number here is defended upstream.
    """
    return allocate_budget(
        year="2026-27",
        # $20.5M cap in 2025-26, 4% annual growth per settlement
        rev_share_cap=21_320_000,
        # UCLA uses the House back-damages formula per Jarmond (LA Times, June 2025)
        sport_shares={
            "Football":          0.75,
            "Men's Basketball":  0.15,
            "Women's Basketball": 0.05,
            "Olympic / Other":   0.05,
        },
        # Third-party NIL layer: collective + brand. LA market premium in play.
        mbb_nil_low=2_000_000,
        mbb_nil_base=3_000_000,
        mbb_nil_high=4_500_000,
        assumptions=[
            "Rev-share cap = $20.5M (2025-26) × 1.04 = $21.3M (2026-27)",
            "Allocation follows Wilken back-damages formula (75/15/5/5)",
            "UCLA commits to full cap per AD Martin Jarmond (LA Times, June 2025)",
            "Third-party NIL range reflects Power Four $3-6M typical layer, "
            "tempered by UCLA's accumulated athletic department debt ($167.7M)",
            "LA market premium plausible but not confirmed by public collective reporting",
        ],
    )


def main() -> None:
    """Run the UCLA 2026-27 scenario from the CLI."""
    alloc = ucla_2026_27_scenario()
    alloc.print_summary()


if __name__ == "__main__":
    main()
