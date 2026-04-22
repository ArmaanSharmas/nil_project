# 04 — The Portal Decision Engine

**Question this section answers:** *When a decision lands on the table — match this offer, chase this portal player, let this guy walk — how should UCLA decide?*

Every portal decision has the same structure:

1. What is this player **worth** to UCLA specifically? (From Section 2.)
2. What does it **cost** to acquire or retain them? (Market price, possibly above #1.)
3. What's the **opportunity cost**? (What else could that money buy?)
4. What's the **roster-fit** adjustment? (Positional need, system fit, locker room.)
5. Decision: **match**, **counter below market**, or **pass**.

The framework formalizes this as a marginal-wins-per-dollar calculation with a roster-fit multiplier. Implementation: `src/portal/decision_engine.py`.

## The scoring function

```
decision_score = (
    expected_marginal_wins * fit_multiplier
    / cost_in_millions
) - opportunity_cost_index
```

Where:
- **expected_marginal_wins** = projected wins this player adds vs. the next-best alternative at a lower cost.
- **fit_multiplier** ranges 0.7 (bad fit) to 1.3 (perfect fit) — positional need, system, locker-room intangibles.
- **cost_in_millions** = the offer you'd need to make.
- **opportunity_cost_index** = how much roster quality you'd sacrifice elsewhere to free up that money (normalized 0–2 scale).

A `decision_score` above ~2.0 is a clear match/acquire. Below 0.8 is a clear pass. The zone in between is where judgment lives — and where the model's biggest value is forcing you to articulate assumptions rather than hide them.

## Scenario framework: three worked examples

These are illustrative scenarios — plug in real 2026 portal names as the window opens. The logic is what matters.

---

### Scenario 1: Retain-or-lose on a rising junior guard

**Situation:** UCLA has a rising junior guard. Valuation model says his market value is **$1.1M**. Another Big Ten school offers **$1.4M**. UCLA's current budget for his slot was **$900K**. Do you match, counter, or pass?

**Inputs:**
- Marginal wins above replacement (a $400K portal wing): **+2.8 wins**
- Fit multiplier: **1.2** (he runs Cronin's system, multi-year relationship)
- Cost to retain: **$1.4M** (must match the outside offer to have any chance; probably $1.35M with the fit premium — a real hometown discount is maybe 5%)
- Opportunity cost: Must reduce two other contracts by $250K each → **high** (cost index: 1.5)

**Calculation (at $1.35M):**
```
(2.8 * 1.2) / 1.35 - 1.5
= 3.36 / 1.35 - 1.5
= 2.49 - 1.5
= 0.99
```

**Decision: BORDERLINE — probably match at $1.35M but only if the $500K reallocation can come from two bench slots without materially hurting depth.** If the cuts have to come from rotation pieces, it's a pass.

**The honest read:** A $1.4M player whose "true" market value is $1.1M is a 27% overpay. You accept overpays for continuity and system fit, but not unlimited overpays. If the offer were $1.6M+, this becomes a clear pass.

---

### Scenario 2: Mid-major All-American hits the portal

**Situation:** A mid-major All-American (think Mountain West POY class, like Dent was in 2025) enters the portal. Your model says **$1.8M**. The market consensus per national reporters is **$2.5M** (bidding war developing).

**Inputs:**
- Marginal wins above alternative: **+4.5 wins** (this is a true impact player)
- Fit multiplier: **1.15** (if he's a PG / combo guard, very strong fit; different number by position)
- Cost: **$2.5M** (can't counter below market — he has multiple $2M+ offers)
- Opportunity cost: eats ~40% of the $6.2M budget → **severe** (cost index: 1.9)

**Calculation:**
```
(4.5 * 1.15) / 2.5 - 1.9
= 5.175 / 2.5 - 1.9
= 2.07 - 1.9
= 0.17
```

**Decision: PASS.** The model says you'd be better off taking that $2.5M and building a balanced top-4 with it. A $2.5M player has to produce *extraordinary* marginal wins — more than 4.5 — to justify the concentration risk. They rarely do at the mid-major-to-P4 jump.

**The caveat:** This calculation changes meaningfully if you already have strong pieces around him. If $2.5M gets him onto a roster that's otherwise complete at the margins, the opportunity cost drops and the decision flips. This is why portal decisions can't be made in isolation from overall roster state.

---

### Scenario 3: Two returners vs. one star (the allocation decision)

**Situation:** You can retain two key returners at $900K each, OR you can let one walk, retain the other at $900K, and spend $1.6M on a portal star.

**Option A: Keep both** ($1.8M spent, two +2.0-win players)
- Combined wins added vs. replacement: 4.0
- Continuity premium: culture, system familiarity, no integration cost
- Ceiling: known, moderately high

**Option B: One returner + portal star** ($0.9M + $1.6M = $2.5M)
- Combined wins added vs. replacement: 2.0 (returner) + 3.5 (star) = 5.5
- Integration cost: portal star + remaining team chemistry = -0.5 wins first 8 games
- Net: 5.0 wins
- Ceiling: higher, with more variance

**But the budgets aren't equal!** Option B costs $700K more. That $700K has to come from somewhere — cutting bench depth, skipping a development player, etc. Call that -1.0 wins worth of lost roster depth.

**Net comparison:**
- Option A: **+4.0 wins, $1.8M, continuity**
- Option B: **+5.0 - 1.0 = +4.0 wins, $2.5M, higher variance**

**Decision: Option A.** Same expected wins, lower cost, less variance. Only flip to Option B if:
(a) the portal star has genuinely unique upside (Final Four swing player), or
(b) the returner being cut isn't actually +2.0 wins and the model was generous.

**The general lesson:** star-chasing looks good on paper because you compare the star to replacement level, not to what you *actually already have*. Retention is almost always underpriced because you're comparing a known quantity to an idealized portal alternative.

---

## The scenario template

Drop new scenarios into `data/raw/portal_scenarios.csv` with these columns:

| Field | Example |
|---|---|
| scenario_id | "2026_04_retain_dent" |
| player | "Donovan Dent" |
| context | "Rising senior, consensus All-American candidate" |
| our_valuation | 2800000 |
| market_price | 3200000 |
| marginal_wins | 4.2 |
| fit_multiplier | 1.25 |
| opportunity_cost_index | 1.7 |
| recommendation | (computed) |

The decision engine outputs `recommendation` and a one-line rationale.

## The honest caveat

Every input above has a confidence interval that the model currently hides. A "+4.5 wins" projection is really "+4.5 ± 2.0 wins." A serious analyst would carry those bands through to the decision. Future work: Monte Carlo the decision function and report the probability that each option is optimal.

---

See `src/portal/decision_engine.py` for the scoring implementation and `data/raw/portal_scenarios.csv` (template) for where to add real 2026 decisions as the portal window opens.
