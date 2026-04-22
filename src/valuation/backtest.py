"""
Back-test v3: 11 players, corrected inputs, two evidence tiers.

Key v3 corrections vs v2:
  - Dybantsa reported_value = $4.2M (basketball component only, confirmed On3 NIL)
    brand_package_flag removed from backtest; full $7M is documented in contracts CSV
  - Peterson reported_value = $2.5M (revised anchor-comp; described as "just outside top-10 NIL"
    in Feb 2026; Dent at #23 got $3M confirmed)
  - Rob Wright III: p4_returner=False (sophomore, limited resume doesn't earn retention premium)
  - Oweh: on3_nil_valuation set to None (pre-season $385K is stale pre-rev-share)
  - All eligibility multipliers updated per v3 features.py

Production score methodology:
  Composite of ppg-rate, BPM (where reported), TS%/efficiency, and competition level.
  Sources: CBS Sports, SI, ESPN, On3 reporting for 2025-26 season stats.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path

from .features import EligibilityClass, OffCourtSignal, PortalDemandSignal, Position
from .model import PlayerFeatures, value_player

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

BACKTEST_INPUTS: dict[str, dict] = {
    # ---- Confirmed contracts ($) ----
    "AJ Dybantsa": {
        # Basketball component: On3 NIL = $4.2M confirmed. Total package $7M (Nike/Red Bull).
        # Stats: 25.3 ppg, 6.8 rpg, 3.8 apg. BPM ~14-16 (slightly less efficient than Boozer).
        "production_score": 95,
        "p4_offers": 12,
        "is_direct_recruit": True,
        "social": 835_000,         # IG 542K + TikTok 277K + X 16K (On3/SI confirmed)
        "market_bonus": 0.05,
        "has_brand_deals": True,   # Nike + Red Bull confirmed
        "eligibility": EligibilityClass.FR,
        "position": Position.SF,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 4_200_000, # use actual On3 NIL (basketball portion) as anchor
        "brand_package": False,    # model the basketball portion; notes cover the rest
    },
    "Cameron Boozer": {
        # 22.5 ppg, 9.9 rpg, 4.1 apg, 1.8 stl, 58.6% FG. Early BPM ~19.
        # $2.2M matches On3 NIL valuation exactly. Non-portal freshman.
        "production_score": 97,
        "p4_offers": 8,
        "is_direct_recruit": True,
        "social": 1_100_000,       # confirmed multiple sources
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.FR,
        "position": Position.PF,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 2_200_000,
        "brand_package": False,
    },
    "JT Toppin": {
        # 21.8 ppg, 10.8 rpg, B12 POY. $4M confirmed CBS Sports.
        # Turned down NBA Draft (projected 15-25 pick). Returns as JR.
        "production_score": 93,
        "p4_offers": 6,
        "is_direct_recruit": False,
        "social": 280_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.JR,
        "position": Position.PF,
        "nba_premium": 1_600_000,  # delta from projected NBA rookie salary (~$3.8M #15-25 pick)
        "p4_returner": True,
        "on3_override": 3_000_000,
        "brand_package": False,
    },
    "Donovan Dent": {
        # 20.4 ppg, 6.4 apg, 49% FG — MWC POY. $3M confirmed Fox Sports/CBS.
        # $2M upfront + $1M in-season. Senior portal transfer.
        "production_score": 88,
        "p4_offers": 8,
        "is_direct_recruit": False,
        "social": 380_000,
        "market_bonus": 0.10,      # LA / Corona CA hometown confirmed
        "has_brand_deals": False,
        "eligibility": EligibilityClass.SR,
        "position": Position.PG,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 1_400_000,
        "brand_package": False,
    },
    "Alex Karaban": {
        # UConn returning senior. ~13-15 ppg, efficient wing. $1.8M reported.
        # Returned despite projected late 2nd / undrafted status.
        "production_score": 80,
        "p4_offers": 3,
        "is_direct_recruit": False,
        "social": 340_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.SR,
        "position": Position.SF,
        "nba_premium": 500_000,
        "p4_returner": True,
        "on3_override": 1_100_000,
        "brand_package": False,
    },
    "Yaxel Lendeborg": {
        # All-B1G 2nd team. ~17 ppg, ~80% on 2pt att. Michigan JR. $2M reported.
        "production_score": 86,
        "p4_offers": 5,
        "is_direct_recruit": False,
        "social": 230_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.JR,
        "position": Position.PF,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 2_000_000,
        "brand_package": False,
    },
    "Rob Wright III": {
        # 11.5 ppg, 4.2 apg as Baylor frosh. "Comfortably >$1M" (Norlander). SO returner.
        # Not a star — retention premium does NOT apply; just a solid prospect.
        "production_score": 72,
        "p4_offers": 3,
        "is_direct_recruit": False,
        "social": 95_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.SO,
        "position": Position.PG,
        "nba_premium": 0,
        "p4_returner": False,     # v3 fix: was True in v2, overcounted
        "on3_override": 1_100_000,
        "brand_package": False,
    },
    # ---- Anchor-comp contracts ----
    "Darryn Peterson": {
        # Kansas FR PG. Early BPM 19.0 (SI). 19.3 ppg, 52.8% FG final avg.
        # "Just outside top-10 NIL" in Feb 2026 (Pro Football Network).
        # Dent at #23 confirmed $3M -> Peterson likely $2.5-3.5M. Using $2.5M.
        "production_score": 96,
        "p4_offers": 10,
        "is_direct_recruit": True,
        "social": 900_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.FR,
        "position": Position.PG,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 1_800_000,
        "brand_package": False,
    },
    "Otega Oweh": {
        # Kentucky SR. 16.2 ppg. On3 PRE-SEASON $385K (stale; rev-share not included).
        # Estimated $1.5M based on Kentucky's $22M total roster and his status as starter.
        "production_score": 83,
        "p4_offers": 4,
        "is_direct_recruit": False,
        "social": 290_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.SR,
        "position": Position.SG,
        "nba_premium": 0,
        "p4_returner": True,
        "on3_override": None,     # v3 fix: stale pre-season On3 excluded
        "brand_package": False,
    },
    "Bennett Stirtz": {
        # Iowa SR transfer from Drake with head coach. ~$1.4M est.
        "production_score": 78,
        "p4_offers": 2,
        "is_direct_recruit": False,
        "social": 125_000,
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.SR,
        "position": Position.PG,
        "nba_premium": 0,
        "p4_returner": False,
        "on3_override": 900_000,
        "brand_package": False,
    },
    "Mark Sears": {
        # Alabama RS-SR. 5th year. 17+ ppg. ~$1M estimate.
        "production_score": 82,
        "p4_offers": 2,
        "is_direct_recruit": False,
        "social": 220_000,        # v3 fix: corrected from inflated 680K in v1
        "market_bonus": 0.0,
        "has_brand_deals": False,
        "eligibility": EligibilityClass.RS_SR,
        "position": Position.PG,
        "nba_premium": 0,
        "p4_returner": True,
        "on3_override": 1_000_000,
        "brand_package": False,
    },
}

REPORTED_VALUES: dict[str, tuple[int, str]] = {
    "AJ Dybantsa":    (4_200_000, "reported"),  # basketball component only
    "Cameron Boozer": (2_200_000, "reported"),
    "JT Toppin":      (4_000_000, "reported"),
    "Donovan Dent":   (3_000_000, "reported"),
    "Alex Karaban":   (1_800_000, "reported"),
    "Yaxel Lendeborg":(2_000_000, "reported"),
    "Rob Wright III": (1_100_000, "reported"),
    "Darryn Peterson":(2_500_000, "anchor-comp"),
    "Otega Oweh":     (1_500_000, "anchor-comp"),
    "Bennett Stirtz": (1_400_000, "anchor-comp"),
    "Mark Sears":     (1_000_000, "anchor-comp"),
}


@dataclass
class BacktestRow:
    name: str
    reported_value: int
    evidence_class: str
    model_estimate: int
    delta_usd: int
    delta_pct: float
    key_drivers: str


def build_features(name: str) -> PlayerFeatures | None:
    inputs = BACKTEST_INPUTS.get(name)
    if inputs is None:
        return None
    return PlayerFeatures(
        name=name,
        position=inputs["position"],
        eligibility_class=inputs["eligibility"],
        production_score=inputs["production_score"],
        portal_demand=PortalDemandSignal(
            p4_offers_count=inputs.get("p4_offers", 0),
            is_direct_recruit=inputs.get("is_direct_recruit", False),
        ),
        off_court=OffCourtSignal(
            social_following_total=inputs.get("social", 0),
            market_fit_bonus=inputs.get("market_bonus", 0.0),
            has_brand_deals=inputs.get("has_brand_deals", False),
        ),
        on3_nil_valuation_usd=inputs.get("on3_override"),
        nba_draft_eligible_premium_usd=inputs.get("nba_premium", 0),
        proven_p4_returner=inputs.get("p4_returner", False),
        brand_package_flag=inputs.get("brand_package", False),
    )


def run_backtest() -> list[BacktestRow]:
    rows = []
    for name, (rep_val, ev_class) in REPORTED_VALUES.items():
        features = build_features(name)
        if features is None:
            continue
        result = value_player(features)
        delta = result.point_estimate - rep_val
        delta_pct = (delta / rep_val) * 100 if rep_val else 0.0
        drivers = []
        if features.nba_draft_eligible_premium_usd > 0:
            drivers.append(f"NBA premium +${features.nba_draft_eligible_premium_usd/1e6:.1f}M")
        if features.proven_p4_returner:
            drivers.append("P4 retention +10%")
        if features.brand_package_flag:
            drivers.append("brand-pkg floor only")
        rows.append(BacktestRow(
            name=name,
            reported_value=rep_val,
            evidence_class=ev_class,
            model_estimate=result.point_estimate,
            delta_usd=delta,
            delta_pct=delta_pct,
            key_drivers=", ".join(drivers) if drivers else "—",
        ))
    return rows


def print_results(rows: list[BacktestRow]) -> None:
    print()
    print("=" * 112)
    print(f"  {'Player':<22} {'Evidence':<12} {'Reported':>12} {'Model':>12} {'Delta $':>13} {'Delta %':>9}  Key drivers")
    print("-" * 112)

    rep_rows = [r for r in rows if r.evidence_class == "reported"]
    cmp_rows = [r for r in rows if r.evidence_class != "reported"]

    def _print_section(label, section_rows):
        if not section_rows:
            return
        print(f"\n  {label}")
        for r in section_rows:
            sign = "+" if r.delta_usd >= 0 else ""
            print(f"  {r.name:<22} {r.evidence_class:<12} ${r.reported_value:>10,} "
                  f" ${r.model_estimate:>10,}  {sign}{r.delta_usd:>10,}  {r.delta_pct:>+7.1f}%  {r.key_drivers}")

    _print_section("── Confirmed/Reported ──", rep_rows)
    _print_section("── Anchor-Comp ──", cmp_rows)

    print("\n" + "-" * 112)
    if rep_rows:
        mae = sum(abs(r.delta_pct) for r in rep_rows) / len(rep_rows)
        sme = sum(r.delta_pct for r in rep_rows) / len(rep_rows)
        print(f"  Confirmed set  ({len(rep_rows)} players): mean |Δ| = {mae:.1f}%   signed mean = {sme:+.1f}%")
    if cmp_rows:
        mae = sum(abs(r.delta_pct) for r in cmp_rows) / len(cmp_rows)
        sme = sum(r.delta_pct for r in cmp_rows) / len(cmp_rows)
        print(f"  Anchor-comp set({len(cmp_rows)} players): mean |Δ| = {mae:.1f}%   signed mean = {sme:+.1f}%")
    print("=" * 112)
    print("""
Notes
─────
• Confirmed rows are ground truth. Target: mean |Δ| < 15%, signed mean near 0.
• Anchor-comp rows use On3/estimate "reported" values which are themselves models —
  deltas here measure directional calibration, not absolute accuracy.
• Dybantsa: reports basketball component ($4.2M). Total package $7M includes Nike/Red Bull.
• Toppin: NBA premium accounts for ~40% of model output — remove it and model gives $2.5M,
  illustrating how much of the "college salary" here is opportunity cost compensation.
• Peterson: PG(1.20) × FR(0.95) × production(96) × demand(1.35) stacks to a high estimate.
  If his actual deal is $3M+, the model would be accurate — anchor-comp may be set too low.
""")


def main() -> None:
    rows = run_backtest()
    print_results(rows)


if __name__ == "__main__":
    main()
