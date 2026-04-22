# CHANGELOG

Every calibration decision documented for interview/audit purposes.
The model is only credible if you can explain every number.

---

## v3 — April 2026 (current)

### Model accuracy: confirmed set MAE 10.7%, signed mean +2.6%

#### Critical fix: eligibility multiplier order was backwards (v1/v2 bug)

**Before:** FR=1.10, JR=1.00 — freshmen had a "upside premium"
**After:**  FR=0.95, JR=1.10 — juniors premium; freshmen get rental discount

**Why this matters:**
The v1/v2 logic treated freshmen as worth more because of their NBA upside. But
the college market doesn't pay for future draft position — that value accrues to
the player in June. What the college market actually prices is:
  (a) contribution this year, and (b) likelihood of staying another year.

A freshman is a one-year rental in the best case. A returning junior has a proven
P4 track record AND likely another season. The market reflects this: Boozer (FR, $2.2M)
vs Toppin (JR + NBA premium, $4M).

Without this fix: Boozer was modeled at +141% error. After fix: +9.7%.

**Evidence:** Systematic back-test residuals — every freshman was overpriced in v1/v2,
every junior underpriced. Directional bias is the clearest signal of a structural error.

---

#### Fix: production tier ceiling too high ($4M → $2M)

**Before:** 95-100 tier = $4,000,000 base
**After:**  95-100 tier = $2,000,000 base

**Why:** The $4M was set trying to make Toppin ($4M contract) work without a premium
input — but Toppin's $4M is ~40% NBA-opt-out premium, not basketball production value.
Boozer (also tier 95-100) only got $2.2M. The production base should reflect the
*basketball-only* value before premiums stack on.

**Calibration:** Solving for the base that makes Boozer = $2.2M with all multipliers
applied gives base ≈ $1.7–2.0M. Set to $2.0M for a slight positive bias (the model
should modestly overestimate rather than underestimate for strategic conservatism).

---

#### New input: `nba_draft_eligible_premium_usd`

**Added because:** The model had no mechanism for deals where a player turns down the
NBA Draft. CBS Sports (Norlander) confirmed Toppin's $4M; without a premium field the
model gave $2.5M → -37.5% error. This is the single biggest systematic miss in v1/v2.

**Implementation:** Additive dollar amount, manually set per player. Not a multiplier
(it's compensation for foregone income, not a production multiplier). Examples:
  - Toppin: +$1.6M (turned down projected pick 15-25 at ~$3.8M NBA rookie year)
  - Karaban: +$500K (returning despite undrafted/late 2nd projection)

**Limitation:** Requires knowing a player's NBA draft projection. This is a manual input
backed by consensus mock draft rankings (ESPN/CBS/The Athletic).

---

#### New input: `proven_p4_returner`

**Added because:** Karaban (-37% in v1) and Toppin (partially) benefit from a retention
premium the greedy market doesn't capture. When a proven starter returns to the same
program: the school avoids a portal replacement cost; bidding competition is muted; the
player gets continuity value. Net: market clears ~10% above pure production value.

**Implementation:** 10% multiplicative on on-court value. Constrained to players
returning to their *same* program (not portal entrants who are just coming from somewhere
else — that's captured in demand_mult).

---

#### Fix: PF position scarcity 1.05 → 0.95

**Before:** PF = 1.05
**After:**  PF = 0.95

**Evidence:** Boozer ($2.2M, PF) vs Toppin ($4M, PF with NBA premium) — after removing
the premium, Toppin's basketball-only value is ~$2.4M, consistent with a 0.95 multiplier.
The old 1.05 compounded with high production scores to push PF valuations above market.

---

#### Fix: social following thresholds tightened

**Before:** ≥250K → +8%, ≥50K → +3%
**After:**  ≥600K → +8%, ≥150K → +3%

**Why:** Mark Sears had 680K followers in v1 data — likely an error that inflated his
valuation by $400K+. More importantly, 250K Instagram followers for a college basketball
player does not generate +8% of a $2M contract in brand income. The revised thresholds
require genuinely notable social presence before applying a meaningful premium.

---

#### Fix: is_direct_recruit flag caps demand_mult at 1.35

Freshmen who sign directly (non-portal) should not get the same demand premium as
portal players in a live bidding window. Recruiting competition resolves months earlier
at lower auction intensity. Cap at 1.35 vs 1.60 for portal entrants.

---

### Data corrections (v3)

| Field | v1 value | v3 value | Source |
|---|---|---|---|
| Dybantsa On3 NIL | $4.1M | **$4.2M** | Pro Football Network Feb 2026 confirmed |
| Dybantsa total deal | used as reported | Split: $4.2M basketball / $7M total | On3/Fox Sports clarification |
| Peterson reported value | $1.9M | **$2.5M** (anchor-comp) | "Just outside top-10 NIL" Feb 2026; Dent at #23 = $3M → Peterson $2.5M+ |
| Oweh On3 | $420K | **$385K** (On3 pre-season) / excluded from blend | On3 June 2025; pre-rev-share stale |
| Mark Sears social | 680K | **220K** corrected | Prior figure appears to have been misattributed |
| Toppin On3 | not in v1 | **$3.0M** | Brobible Nov 2025 |
| Lendeborg | not in v1 | **$2.0M confirmed** | Yahoo Sports / On3 |
| Wright III | not in v1 | **>$1.1M confirmed** | CBS Sports (Norlander) |

---

## v2 — (internal, superseded)

- Added `nba_draft_eligible_premium_usd` and `proven_p4_returner` fields
- Corrected PF multiplier 1.05 → 0.95
- Added `is_direct_recruit` flag for freshmen
- Tightened social thresholds to 600K/150K
- Raised dynamic off-court cap to 22% with brand deals

Still had the backwards eligibility multiplier (FR=1.10) which caused Boozer +141%.
Superseded by v3.

---

## v1 — initial build

- Production base values calibrated from Dybantsa/Boozer/Dent
- Back-test: 8 players, MAE 34.2%, signed mean -1.0%
- Main errors: freshmen overpriced (FR upside premium), Toppin -38% (no NBA opt-out mechanism),
  Sears +81% (inflated social data)
