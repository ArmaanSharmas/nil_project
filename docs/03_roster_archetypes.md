# 03 — Roster Construction Archetypes

**Question this section answers:** *Given a $6.2M budget and 15 roster spots, what spending shapes give you the best shot at winning?*

This is the strategy layer. There's no "optimal" answer independent of your goals — a program chasing a Final Four has a different optimum than one trying to build multi-year continuity. Three archetypes, each parameterized in `src/roster/archetypes.py`:

## Archetype A: Stars and Scrubs

**Shape:** One $2.0–2.5M superstar, one $1.2M secondary star, thirteen players between $80K and $350K.

**Example allocation on $6.2M budget:**

| Slot | Role | Salary |
|---|---|---|
| 1 | Superstar (likely lottery-track) | $2,200,000 |
| 2 | Secondary star | $1,100,000 |
| 3 | Starter-caliber guard | $550,000 |
| 4 | Starter-caliber wing | $450,000 |
| 5 | Starter-caliber big | $400,000 |
| 6-8 | Rotation (8-15 min/game) | $220,000 × 3 = $660,000 |
| 9-11 | End of bench / spot-play | $130,000 × 3 = $390,000 |
| 12-15 | Developmental / redshirt / walk-on+ | $90,000 × 4 = $360,000 |
| **Total** | | **$6,110,000** |

**When to run it:**
- You have a realistic shot at landing a top-10 player or retaining a breakout star.
- You're in a one-year window (coaching seat hot, NCAA berth critical).
- You have a clear offensive system that can force-feed a star (high-usage possession model).

**Why it works:**
- March basketball is star-driven. Half-court creation in the tournament is everything.
- Single-elimination variance rewards ceiling over floor.

**Why it fails:**
- One injury to the star and the season is over.
- Elite stars leave after one year; you rebuild the roster around nothing.
- Recruiting role players at $130K–$350K is genuinely hard; talent gap between your stars and bench is jarring.

## Archetype B: Balanced Veteran

**Shape:** Three $1.0M+ proven veterans, four $400K-$600K starters, rotation and bench filled sensibly. No mega-contract.

**Example allocation on $6.2M budget:**

| Slot | Role | Salary |
|---|---|---|
| 1 | Proven starter A (high-major senior PG) | $1,200,000 |
| 2 | Proven starter B (wing scorer) | $1,100,000 |
| 3 | Proven starter C (big with skill) | $1,000,000 |
| 4 | Starter-caliber role | $550,000 |
| 5 | Starter-caliber role | $500,000 |
| 6-7 | 6th/7th man | $300,000 × 2 = $600,000 |
| 8-10 | Rotation | $180,000 × 3 = $540,000 |
| 11-13 | Developmental | $120,000 × 3 = $360,000 |
| 14-15 | Walk-on+ / redshirt | $70,000 × 2 = $140,000 |
| **Total** | | **$5,990,000** |

**When to run it:**
- You have a coaching staff that maximizes role clarity (Cronin fits this archetype well).
- You're chasing Sweet 16+ consistency rather than swinging for a Final Four.
- You have a stable pipeline of 3-star-plus high schoolers developing into juniors.

**Why it works:**
- Floor is higher — three proven players compound fewer "bad nights" across a season.
- Fewer catastrophic injuries (no single point of failure).
- Better in conference play where games are grindy.

**Why it fails:**
- Ceiling is lower. Without a true star, tournament runs require perfect matchups.
- Senior-heavy rosters turn over completely; rebuilds are harsh.
- In the portal era, paying three $1M+ players is a *lot* of opportunity cost against one $3M star.

## Archetype C: Development Flywheel

**Shape:** No contract over $800K. Heavy investment in upside freshmen and sophomores. Bet on internal growth and coaching development.

**Example allocation on $6.2M budget:**

| Slot | Role | Salary |
|---|---|---|
| 1 | Top freshman (projected Day 1 starter) | $800,000 |
| 2 | High-upside sophomore | $650,000 |
| 3 | Proven junior returner | $600,000 |
| 4 | Another high-upside soph | $550,000 |
| 5 | Freshman with starter ceiling | $500,000 |
| 6-8 | Rotation freshmen/sophs | $320,000 × 3 = $960,000 |
| 9-11 | Upside reserves | $220,000 × 3 = $660,000 |
| 12-15 | Development / redshirt | $130,000 × 4 = $520,000 |
| **Total** | | **$5,840,000** |

**When to run it:**
- Your coaching staff has a proven track record of player development (Cronin at Cincinnati had this; it's less clear at UCLA so far).
- You're building for a Year 3–4 peak, not Year 1.
- You're okay with a losing season as the cost of compound growth.

**Why it works:**
- Compounding. Year 2 and Year 3 versions of the same players are dramatically better.
- Lower per-player salaries mean you can absorb a transfer loss without gutting the budget.
- In the long run, this is how programs like Gonzaga outperformed their spending power.

**Why it fails:**
- Modern college basketball is *hostile* to patience. Transfer portal means your developed sophomore leaves for $1.5M elsewhere.
- Coaches get fired waiting for Year 3.
- Fanbase / booster patience evaporates after one losing season.

## Which archetype for UCLA 2026-27?

Each archetype has a quantitative profile in `src/roster/archetypes.py`:

```python
@dataclass
class Archetype:
    name: str
    exp_wins_mean: float
    exp_wins_std: float         # <- variance; higher = more upside/downside
    multi_year_ev: float        # <- expected "wins carried forward" to year+1
    injury_sensitivity: float   # <- win-loss swing per lost-game of a top player
```

Illustrative values (to be calibrated with actual Bart Torvik / KenPom data once a specific roster is built):

| Archetype | Exp. Wins | Std Dev | Multi-Year EV | Injury Sensitivity |
|---|---|---|---|---|
| Stars and Scrubs | 22.0 | 4.5 | Low | **High** |
| Balanced Veteran | 23.5 | 2.8 | Medium | Medium |
| Development Flywheel | 19.5 | 3.5 | **High** | Low |

**Reading this:** Balanced Veteran has the highest expected wins *this season* but Stars and Scrubs has the highest *ceiling*. Flywheel is the worst one-year bet but has the best multi-year trajectory.

**Recommendation for UCLA 2026-27:** A modified **Balanced Veteran** with one stars-and-scrubs lean — specifically, Cronin's defensive system rewards veteran guards, but UCLA's market (LA, brand, weather) makes it a realistic landing spot for one elite portal player per cycle. See Section 5 for the actual implementation.

## The tradeoff in one chart

```
         ↑ Ceiling (Final Four odds)
         │
    Stars│    ● 
    & Scr│       
         │                       ● Balanced
         │                         Veteran
         │                                                
         │                                       ● Flywheel
         │                                        (Year 3)
         │                                                
         └──────────────────────────────────────→ Floor (missing tournament odds)
```

Stars & Scrubs is top-left (high ceiling, low floor). Balanced Veteran is middle. Flywheel is bottom-right short-term and moves diagonally toward the top over 3 years.

---

See `src/roster/archetypes.py` for the parameterized builders and `src/roster/constructor.py` for the cap-constrained optimization that fills each archetype with actual (or hypothetical) players.
