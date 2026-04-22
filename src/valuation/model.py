"""
Core player valuation model — v2.

New inputs in v2:
  nba_draft_eligible_premium_usd: explicit dollar add-on for players who
    turned down the NBA Draft to return to college. This is the single
    biggest missing factor in v1 — Toppin ($4M) and Karaban ($1.8M) both
    had this premium baked into their contracts. Without it, the model
    systematically underpriced any player who could have left early.

  proven_p4_returner: boolean for starters returning to the SAME program
    (not transferring). Adds a 10% retention markup. Rationale: the program
    avoids a replacement search in the portal, the player gains system
    continuity, and bidding competition is muted (the school is the only
    buyer). Market clears slightly above pure production value.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

from .features import (
    Position, EligibilityClass,
    POSITION_SCARCITY, ELIGIBILITY_MULTIPLIER,
    PortalDemandSignal, OffCourtSignal,
    production_base_value,
)

Confidence = Literal["Low", "Medium", "High"]


@dataclass
class PlayerFeatures:
    name: str
    position: Position
    eligibility_class: EligibilityClass

    production_score: float   # 0-100 composite: BPR / PRPG! / KenPom metrics

    portal_demand: PortalDemandSignal = field(default_factory=PortalDemandSignal)
    off_court: OffCourtSignal = field(default_factory=OffCourtSignal)
    on3_nil_valuation_usd: int | None = None

    # ---- v2 new fields ----
    nba_draft_eligible_premium_usd: int = 0
    """
    Dollar amount added for players who turned down NBA Draft entry.
    This is a direct market observation: schools must compensate the player
    for their foregone NBA income. Set to the estimated delta between the
    player's projected NBA rookie contract and their best outside offer.
    Examples: Toppin +$1.6M (turned down projected 15-25 pick), Karaban +$500K.
    """
    proven_p4_returner: bool = False
    """
    True if the player is a returning starter at their CURRENT program
    (not a portal entrant). Applies a 10% retention premium on the base value.
    """

    previous_contract_usd: int | None = None
    best_outside_offer_usd: int | None = None
    brand_package_flag: bool = False


@dataclass
class ValuationResult:
    player_name: str
    point_estimate: int
    low_band: int
    high_band: int
    reservation_price: int | None
    confidence: Confidence

    # Auditability breakdown
    base_value: int
    position_multiplier: float
    eligibility_multiplier: float
    portal_demand_multiplier: float
    off_court_bump: int
    on3_anchor_delta: int
    nba_premium_applied: int
    retention_premium_applied: int

    notes: list[str] = field(default_factory=list)

    def summary_line(self) -> str:
        return (
            f"{self.player_name:30s}  "
            f"${self.point_estimate:>10,}  "
            f"[${self.low_band:>10,} – ${self.high_band:>10,}]  "
            f"conf={self.confidence}"
        )


def value_player(features: PlayerFeatures) -> ValuationResult:
    notes: list[str] = []

    # Step 1: production base
    base = production_base_value(features.production_score)

    # Step 2: position scarcity
    pos_mult = POSITION_SCARCITY.get(features.position, 1.0)

    # Step 3: eligibility
    elig_mult = ELIGIBILITY_MULTIPLIER.get(features.eligibility_class, 1.0)

    # Step 4: portal demand
    demand_mult = features.portal_demand.premium_multiplier()

    on_court_value = int(round(base * pos_mult * elig_mult * demand_mult))

    # Step 5: proven P4 returner premium (+10% on on_court_value)
    retention_premium = 0
    if features.proven_p4_returner:
        retention_premium = int(on_court_value * 0.10)
        on_court_value += retention_premium

    # Step 6: off-court bump
    off_court_bump = features.off_court.additive_bump(on_court_value)
    subtotal = on_court_value + off_court_bump

    # Step 7: NBA draft eligible premium (additive, not multiplicative)
    nba_premium = features.nba_draft_eligible_premium_usd
    subtotal += nba_premium

    if nba_premium > 0:
        notes.append(
            f"NBA draft eligible premium of ${nba_premium:,} applied. "
            "This reflects compensation for foregone draft income — "
            "not purely basketball production."
        )

    # Step 8: On3 anchor blend (10%)
    on3_delta = 0
    if features.on3_nil_valuation_usd is not None:
        anchor = features.on3_nil_valuation_usd
        blended = int(round(0.90 * subtotal + 0.10 * anchor))
        on3_delta = blended - subtotal
        subtotal = blended

        if anchor > 0 and subtotal > 0:
            ratio = max(anchor, subtotal) / min(anchor, subtotal)
            if ratio > 3.0:
                notes.append(
                    f"On3 anchor (${anchor:,}) diverges >3x from on-court estimate. "
                    "Review inputs or flag as brand-package outlier."
                )

    # Step 9: brand-package flag
    if features.brand_package_flag:
        notes.append(
            "brand_package_flag=True: output is a FLOOR. "
            "Total brand deals (Nike/Red Bull/apparel) can 2-3x the basketball salary component."
        )

    point_estimate = subtotal
    low_band = int(round(point_estimate * 0.85))
    high_band = int(round(point_estimate * 1.15))
    reservation = _reservation_price(features, point_estimate)
    confidence = _assess_confidence(features)

    return ValuationResult(
        player_name=features.name,
        point_estimate=point_estimate,
        low_band=low_band,
        high_band=high_band,
        reservation_price=reservation,
        confidence=confidence,
        base_value=base,
        position_multiplier=pos_mult,
        eligibility_multiplier=elig_mult,
        portal_demand_multiplier=demand_mult,
        off_court_bump=off_court_bump,
        on3_anchor_delta=on3_delta,
        nba_premium_applied=nba_premium,
        retention_premium_applied=retention_premium,
        notes=notes,
    )


def _reservation_price(features: PlayerFeatures, point_estimate: int) -> int | None:
    candidates: list[int] = []
    if features.previous_contract_usd:
        candidates.append(int(features.previous_contract_usd * 1.10))
    if features.best_outside_offer_usd:
        candidates.append(int(features.best_outside_offer_usd * 0.90))
    if point_estimate >= 2_000_000:
        candidates.append(1_400_000)
    elif point_estimate >= 1_000_000:
        candidates.append(750_000)
    elif point_estimate >= 400_000:
        candidates.append(250_000)
    elif point_estimate >= 150_000:
        candidates.append(100_000)
    else:
        candidates.append(50_000)
    return max(candidates) if candidates else None


def _assess_confidence(features: PlayerFeatures) -> Confidence:
    signals = sum([
        features.on3_nil_valuation_usd is not None,
        features.portal_demand.p4_offers_count > 0 or features.portal_demand.on3_portal_rank is not None,
        features.previous_contract_usd is not None or features.best_outside_offer_usd is not None,
        features.off_court.social_following_total > 0,
    ])
    if signals >= 3:
        return "High"
    if signals >= 2:
        return "Medium"
    return "Low"
