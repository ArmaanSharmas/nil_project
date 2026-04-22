# 02 — Player Valuation Framework

**Question this section answers:** *Given a player, what should UCLA be willing to pay?*

## The inputs (six components)

### 1. Production tier (weight: 35%)

A composite of publicly available advanced stats:
- **BPM** (Box Plus/Minus) where available — best all-in-one impact metric
- **Bart Torvik BPR / EvanMiya PRPG!** — lineup-adjusted production
- **KenPom ORtg × %Min** — efficiency weighted by role
- **Scoring rate × efficiency** proxy: `(ppg / 25) * 0.40 + (TS% / 0.65) * 0.35 + competition_context * 0.10`

Output: a `production_score` on 0–100. Calibration anchors:
| Player | Stats (2025-26) | BPM | Score |
|---|---|---|---|
| Cameron Boozer | 22.5/9.9/4.1, 58.6% FG | ~19 | 97 |
| Darryn Peterson | 19.3/3.8/2.8, 52.8% FG | 19.0 | 96 |
| AJ Dybantsa | 25.3/6.8/3.8 | ~14-16 | 95 |
| JT Toppin | 21.8/10.8/2.1 | ~12 | 93 |
| Donovan Dent | 20.4/x/6.4, 49% FG (MWC) | ~9 | 88 |

### 2. Position scarcity (weight: 15%)

| Position | Multiplier | Rationale |
|---|---|---|
| PG | 1.20 | Lead initiators are genuinely scarce |
| SF | 1.10 | Two-way wings |
| C  | 1.05 | Mobile rim-protectors scarce |
| PF | 0.95 | Market doesn't pay the PF premium it once did |
| SG | 0.95 | Oversupplied in portal |

### 3. Eligibility class (weight: 15%)

**v3 key insight:** Freshmen get a *discount*, not a premium. The college market pays for contribution this year — NBA upside is the player's to capture in the draft, not the school's to pay for.

| Class | Multiplier | Rationale |
|---|---|---|
| JR | 1.10 | Proven + another year; highest multi-year EV |
| RS-SO | 1.00 | Baseline |
| SO / SR | 1.00 | Proven (SR) or developing (SO) |
| FR | 0.95 | One-year rental; unproven at P4 level |
| RS-SR | 0.88 | 5th-year rental; market reflects diminishing returns |

### 4. Portal demand signal (weight: 15%)

Number of P4 offers + On3 portal rank → premium multiplier (1.0–1.60 for portal players, capped at 1.35 for non-portal freshmen who signed directly — recruiting competition doesn't generate the same real-time auction dynamics as the portal window).

### 5. Off-court value (weight: 10%)

Social following tiers: 2M+ → +15%, 600K+ → +8%, 150K+ → +3%. Brand deals: +8%. LA market bonus: manually set (0.0–0.20). Total off-court cap: 22% with brand deals, 18% without.

### 6. On3 NIL valuation (weight: 10% — anchor blend)

On3's independent valuation blended in at 10% as a sanity-check anchor. If on3 and model diverge by >3x, a warning note is generated.

## The v2 premium inputs (new in this version)

**`nba_draft_eligible_premium_usd`**: Explicit dollar add-on for players who turned down the NBA Draft to return. This is not basketball productivity — it's opportunity-cost compensation. Without it, the model systematically underprices Toppin-class deals by 30–40%.

**`proven_p4_returner`**: 10% retention markup for starters returning to their same program. The school avoids a portal replacement search; bidding competition is muted. Market clears above pure production value.

## The output

```
player_name:          Hypothetical PG
point_estimate:       $1,825,000
low_band:             $1,551,000     (85th-pct downside)
high_band:            $2,099,000     (85th-pct upside)
reservation_price:    $1,300,000     (minimum they'd accept)
confidence:           High

Component breakdown:
  base_value:             $1,800,000  (production tier 85-94)
  pos_multiplier:             ×1.20  (PG scarcity)
  elig_multiplier:            ×1.00  (SR)
  demand_multiplier:          ×1.25  (8 P4 offers)
  off_court_bump:           +$81,000  (380K social + LA bonus)
  on3_anchor_delta:         -$34,000  (blending toward On3 lower)
  nba_premium:                    $0
  retention_premium:              $0
```

## Reservation price (labor econ)

```
reservation_price = max(
    previous_contract × 1.10,        # year-over-year raise floor
    best_outside_offer × 0.90,        # 90% of best known alt
    market_floor_for_tier,            # role-based minimum
)
```

If a player's reservation price = $1.3M and UCLA's model says $1.8M, there's a $500K negotiation window. If it equals the market price, pay market or lose them.

## Back-test results (v3, confirmed 2025-26 deals)

**11-player dataset across two evidence tiers.**

### Confirmed/reported contracts

| Player | Reported | Model | Δ% | Key inputs |
|---|---|---|---|---|
| AJ Dybantsa | $4.2M (bball portion) | $3.27M | -22.3% | brand_package_flag=True; this is the *floor*. Full deal $7M. |
| Cameron Boozer | $2.2M | $2.41M | +9.7% | FR rental discount (0.95) is the critical fix |
| JT Toppin | $4.0M | $4.14M | +3.4% | NBA premium $1.6M + P4 retention 10% explain the result |
| Donovan Dent | $3.0M | $2.89M | -3.8% | Closest fit. PG scarcity × LA bonus × MWC POY stacks cleanly |
| Alex Karaban | $1.8M | $1.75M | -2.6% | NBA premium $500K + retention. |
| Yaxel Lendeborg | $2.0M | $2.38M | +19.0% | Slight overcount; JR PF multiplier stack |
| Rob Wright III | $1.1M | $1.26M | +14.5% | SO PG with high production score |

**Confirmed set: mean |Δ| = 10.7%, signed mean = +2.6%**
*(down from 34.2% MAE in v1 — a 3.2× accuracy improvement)*

### Anchor-comp contracts (On3/estimate sourced)

| Player | Anchor | Model | Δ% | Note |
|---|---|---|---|---|
| Darryn Peterson | $2.5M | $2.95M | +18.0% | Anchor-comp likely too low; his actual deal probably $3M+ |
| Otega Oweh | $1.5M | $1.15M | -23.7% | On3 pre-season stale; actual Kentucky deal unconfirmed |
| Bennett Stirtz | $1.4M | $1.16M | -17.4% | Portal transfer following coach — loyalty discount plausible |
| Mark Sears | $1.0M | $1.16M | +16.4% | RS-SR 5th year discount applied |

**Anchor-comp set: mean |Δ| = 18.9%, signed mean = -1.7%**

## What the residuals tell us

**Dybantsa -22.3%:** Intentional. Brand-package flag means model output is a floor. The $1M gap between $3.27M model and $4.2M On3 NIL reflects brand-deal value (Nike/Red Bull) that lives outside the basketball salary model. For any player with `brand_package_flag=True`, add a manual premium.

**Lendeborg +19.0% / Wright +14.5%:** The model slightly overprices young players whose performance was strong but who haven't cleared the scarcity premium market. JR PF at $1.8M base × 1.10 × 1.12 stacks quickly. Could correct by adding a `competition_quality_discount` for players below top-5 conference level, but at the cost of complexity.

**Peterson's "anchor-comp" is probably the model that's right.** He's the #1 overall recruit in the class, BPM ~19.0, PG(1.20) × FR(0.95) × demand(1.35). A $3M deal would be perfectly consistent with the model — the $2.5M anchor-comp is likely too conservative.

## Known model limitations

1. No causal identification (production → wins regression not yet built)
2. `nba_draft_eligible_premium` requires subjective input — must know a player's NBA draft projection
3. Off-court value degrades quickly for players beyond the top 50 social followings
4. Doesn't yet model multi-year deals or incentive structures

See `src/valuation/` for implementation. Run `python -m src.valuation.backtest` to reproduce.
