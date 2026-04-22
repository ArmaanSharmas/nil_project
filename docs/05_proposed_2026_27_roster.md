# 05 — Proposed 2026-27 UCLA Roster

**Budget:** $6.2M base case. **Strategy:** Modified Balanced Veteran (see Section 3).

## The portal window context (April 2026)

The 2026 transfer portal opened April 7 and closes April 21. This section is built on real available players. Key market data from On3, CBS Sports, and NBC Sports:

**Top 2026 portal players (confirmed):**
- **Flory Bidunga** (Kansas C, SO): 13.3 PPG / 9.0 RPG / 2.6 BPG / 64% FG. On3 NIL $2.1M. Elite defensive anchor. *Committed to Louisville.*
- **John Blackwell** (Wisconsin SG, JR): 19.1 PPG / 5.1 RPG. On3 NIL $1.5M. 26 PPG in B1G Tournament. Considering Duke or Illinois.
- **Rob Wright III** (BYU PG, SO): 18.1 PPG / 4.6 APG in 2025-26. Interest from Kentucky, Arkansas, Ohio State.
- **PJ Haggerty** (Kansas State, RS-JR): On3 NIL $2.6M. 94 of last 96 games in double figures. *Committed to Texas A&M.*
- **Milan Momcilovic** (Iowa State PF, JR): On3 NIL $2.0M. Testing NBA Draft + portal.
- **Massamba Diop** (Arizona State C, FR): On3 NIL $2.0M. 13.6 PPG / 5.8 RPG.

## UCLA's gap analysis

2025-26 departing seniors: Donovan Dent (PG), Skyy Clark (SG), Jamar Brown (SF), Steven Jamerson II (C).

**Priority needs:**
1. **Lead PG** — Dent's replacement. Most critical. Without a $1.5M+ portal PG, the offense regresses.
2. **Scoring wing** — Brown's replacement at the SF spot.
3. **Frontcourt depth** — if Booker's development stalls, one more big.

## Portal decision engine results (real 2026 scenarios)

Run `python -m src.portal.decision_engine` for live scores. From the v3 CSV:

| Scenario | Score | Decision |
|---|---|---|
| Retain Bilodeau at $1.4M | 0.90 | **COUNTER** — try to retain below $1.4M |
| Rob Wright III at $2.0M | 1.10 | **COUNTER** — positive but market at 1.25x our valuation |
| John Blackwell at $1.8M | 1.00 | **COUNTER** — scoring guard but not primary positional need |
| Momcilovic at $2.4M | 0.52 | **PASS** — opportunity cost too high for another PF |

## The proposed 15-man roster (2026-27)

**Base case: $6.2M budget | Strategy: Balanced Veteran**

| # | Player | Class | Pos | Role | Contract | Basis |
|---|---|---|---|---|---|---|
| 1 | **Rob Wright III (portal target)** | JR | PG | Starter — Primary creator | **$1.8M** | Valuation model + portal demand. Kentucky/Ohio State competing; our fit premium justifies slight overpay vs. $1.6M valuation. |
| 2 | **Tyler Bilodeau** | SR | PF | Starter — Anchor scorer | **$1.1M** | Retain. All-Pacific District 1st team. Counter below $1.4M market ask. |
| 3 | **Xavier Booker** | JR | C | Starter — Rim protection | **$800K** | Retain JR. Improved sophomore → junior leap. |
| 4 | **Eric Dailey Jr.** | SR | SF | Starter — Two-way wing | **$750K** | Retain. Proven Cronin-system fit. |
| 5 | **TBD portal SG/SF** | SR | SG/SF | Starter — Scoring guard | **$550K** | Blackwell's market is $1.8M (portal engine: PASS at that price). Target a tier-2 portal scorer or mid-major wing with a UCLA fit. Blackwell is aspirational if he takes below-market for fit/brand.| |
| 6 | **Brandon Williams** | JR | SG | Rotation — Off-ball shooter | **$420K** | Retain. Year 3 development should unlock starter minutes. |
| 7 | **TBD — portal wing** | SR | SF | Rotation | **$350K** | Mid-tier portal target; depth behind Dailey. |
| 8 | **Eric Freeny** | SO | G | Rotation | **$200K** | Retain development bet. |
| 9 | **TBD — portal or FR** | FR/SO | PG | Reserve guard | **$200K** | Backup PG insurance. |
| 10 | **TBD — portal big** | varies | C | Reserve | **$180K** | Foul insurance at the 5. |
| 11 | **TBD — FR signee** | FR | SF | Developmental | **$150K** | 2026 signing class. |
| 12 | **TBD — FR signee** | FR | PG | Developmental | **$130K** | 2026 signing class. |
| 13 | **Lino Mark** | JR | PG | Developmental | **$120K** | Retain reserve PG. |
| 14 | **TBD** | FR | PF | Developmental | $90K | Development. |
| 15 | **Walk-on+** | — | — | Developmental | $60K | Program piece. |
| | **Total** | | | | **$6,950,000** | ~$750K over base |

**Budget reconciliation:** The $6.95M build is $750K over the $6.2M base case. Resolution paths:
- Negotiate Bilodeau to $1.0M (retention leverage if offers are genuinely at $1.4M but no one has closed) → saves $100K
- Reduce Wright target to $1.6M and accept they might not get him → saves $200K
- Push third-party NIL layer upward toward high-case $4.5M → raises total budget to $6.7M
- Counter Blackwell at $500K instead of $600K → saves $100K

Realistic path: land Wright at $1.7M, Bilodeau at $1.0M, collective supplements ~$600K. Total lands at $6.6M.

## Projected starting five and record

**Starting five:**
1. Rob Wright III (PG) — primary creator, 18 PPG upside
2. John Blackwell (SG) — scoring guard, high B1G production
3. Eric Dailey Jr. (SF) — two-way, system veteran
4. Tyler Bilodeau (PF) — stretch 4, go-to scorer
5. Xavier Booker (C) — rim protection, improving

**Archetype parameters (Balanced Veteran):** Projected 23.5 wins, std 2.8.
**Realistic range:** 21–26 wins, top-6 Big Ten, Sweet 16 realistic, Elite 8 ceiling.

## What could break this

1. **Wright goes to Kentucky/Ohio State.** Contingency: pivot to a lower-tier portal PG at $1.2M and use the saved $600K to improve the bench. Record drops to 20–22 wins without a true creator.
2. **Bilodeau's market is genuinely $1.4M.** Decision engine says COUNTER, not MATCH. If Kentucky bids $1.5M, let him walk and rebuild around Booker + portal SF at $1.3M.
3. **Retention rate below 60%.** If Dailey or Booker transfer, this roster needs a complete re-run through the constructor.

---

*Run `python -m src.portal.decision_engine` to score the real 2026 scenarios. Update `data/raw/portal_scenarios.csv` as the portal window closes (April 21, 2026).*
