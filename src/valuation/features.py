"""
Feature definitions and enumerations — v3 (final calibration).

Core insight that drove v1/v2 overpricing of freshmen:
  The eligibility multiplier was backwards. FR = 1.10 (premium) reflected
  "NBA upside value" — but colleges pay for contributions THIS YEAR, not
  future draft position. That's the player's to capture in the NBA.
  A freshman is a one-year rental; a returning junior is a multi-year asset
  AND has a proven track record. The correct ordering is:

    JR: 1.10 (premium: proven + likely another year)
    FR: 0.95 (slight discount: one-year rental, unproven at P4)
    SR: 1.00 (proven, but one year)
    SO: 1.00 (limited proof, one more year likely)
    RS_SR: 0.88 (5th-year rental with declining marginal wins)

  This single change brings Boozer from +141% to ~+10%, which is the
  correct result: a $2.2M contract for an elite freshman.

Production base values also corrected:
  95-100: $2.0M (down from $4.0M in v2 / $3.0M in v1)
  Calibrated so that FR elite player (Boozer) with all multipliers
  produces ~$2.2M before On3 blend, matching his reported contract.

Position scarcity unchanged from v2 (PF 0.95, PG 1.20).
Social thresholds and off-court cap unchanged from v2.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Final


class Position(str, Enum):
    PG = "PG"
    SG = "SG"
    SF = "SF"
    PF = "PF"
    C  = "C"


class EligibilityClass(str, Enum):
    FR     = "FR"
    SO     = "SO"
    JR     = "JR"
    SR     = "SR"
    RS_FR  = "RS-FR"
    RS_SO  = "RS-SO"
    RS_JR  = "RS-JR"
    RS_SR  = "RS-SR"


# v3: PG=1.20, SG=0.95, SF=1.10, PF=0.95, C=1.05
POSITION_SCARCITY: Final[dict[Position, float]] = {
    Position.PG: 1.20,
    Position.SG: 0.95,
    Position.SF: 1.10,
    Position.PF: 0.95,
    Position.C:  1.05,
}

# v3: JR gets the premium (proven + multi-year); FR gets rental discount
ELIGIBILITY_MULTIPLIER: Final[dict[EligibilityClass, float]] = {
    EligibilityClass.FR:    0.95,   # one-year rental; market pays for this year
    EligibilityClass.SO:    1.00,   # baseline
    EligibilityClass.JR:    1.10,   # proven + another year likely; highest EV
    EligibilityClass.SR:    1.00,   # proven, one year — market pays full
    EligibilityClass.RS_FR: 0.97,
    EligibilityClass.RS_SO: 1.00,
    EligibilityClass.RS_JR: 1.05,
    EligibilityClass.RS_SR: 0.88,  # 5th-year: rental with diminishing returns
}

# v3: top tier $4M -> $2M. Calibrated against Boozer ($2.2M confirmed).
PRODUCTION_BASE_VALUES: Final[list[tuple[int, int, int]]] = [
    (95, 100, 2_000_000),   # elite lottery-track (Boozer/Dybantsa/Peterson class)
    (85, 94,  1_800_000),   # P4 All-Conference starter (Toppin before premiums)
    (70, 84,    950_000),   # P4 reliable starter (Karaban, Oweh)
    (55, 69,    460_000),   # P4 rotation / mid-major star
    (40, 54,    210_000),   # P4 bench
    (0,  39,     90_000),   # developmental
]


def production_base_value(production_score: float) -> int:
    score = max(0.0, min(100.0, production_score))
    for lo, hi, val in PRODUCTION_BASE_VALUES:
        if lo <= score <= hi:
            return val
    return 90_000


COMPONENT_WEIGHTS: Final[dict[str, float]] = {
    "production":        0.35,
    "position_scarcity": 0.15,
    "eligibility":       0.15,
    "portal_demand":     0.15,
    "off_court":         0.10,
    "on3_anchor":        0.10,
}


@dataclass
class PortalDemandSignal:
    """
    is_direct_recruit: non-transfer freshman.
    Caps demand_mult at 1.35 (recruiting does not have the same real-time
    auction dynamics as the portal bidding window).
    """
    p4_offers_count: int = 0
    on3_portal_rank: int | None = None
    reported_asking_price: int | None = None
    is_direct_recruit: bool = False

    def premium_multiplier(self) -> float:
        base = 1.0
        if self.p4_offers_count >= 5:
            base += 0.25
        elif self.p4_offers_count >= 3:
            base += 0.12
        elif self.p4_offers_count >= 1:
            base += 0.04

        if self.on3_portal_rank is not None:
            if self.on3_portal_rank <= 10:
                base += 0.20
            elif self.on3_portal_rank <= 25:
                base += 0.10
            elif self.on3_portal_rank <= 50:
                base += 0.03

        cap = 1.35 if self.is_direct_recruit else 1.60
        return min(base, cap)


@dataclass
class OffCourtSignal:
    """
    v3: social tiers 600K / 150K. Off-court cap 22% w/ brand deals, 18% without.
    """
    social_following_total: int = 0
    market_fit_bonus: float = 0.0
    has_brand_deals: bool = False

    def additive_bump(self, base_value: int) -> int:
        bump = 0.0
        if self.social_following_total >= 2_000_000:
            bump += 0.15
        elif self.social_following_total >= 600_000:
            bump += 0.08
        elif self.social_following_total >= 150_000:
            bump += 0.03

        bump += self.market_fit_bonus
        if self.has_brand_deals:
            bump += 0.08

        cap = 0.22 if self.has_brand_deals else 0.18
        bump = min(bump, cap)
        return int(base_value * bump)
