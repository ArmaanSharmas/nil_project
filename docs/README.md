# UCLA Men's Basketball — Rev-Share & Roster Construction Model

A full GM-style operating model for UCLA Men's Basketball: budget allocation under the House settlement cap, a player market valuation framework, a portal decision engine, and a defensible 2026-27 roster built within realistic constraints.

## The pitch

The House v. NCAA settlement took effect July 1, 2025, making 2025-26 the first year schools could directly share revenue with athletes (up to $20.5M, growing ~4% annually). Nearly all Power Four schools — UCLA included — are funding the full cap. The open question is no longer *whether* to pay players, but *how to allocate a basketball budget like a front office*.

This project treats UCLA MBB as a cap-managed franchise and builds the analytical tools a college GM actually needs:

1. A defensible top-down **budget allocation** from athletic revenue → football/MBB/women's/Olympic → individual player contracts.
2. A **player valuation model** that takes production, position, eligibility, portal demand, and off-court inputs and returns a market value with a confidence band.
3. A **roster construction layer** that compares strategic archetypes (stars-and-scrubs vs. balanced vs. development flywheel) under a hard cap.
4. A **portal decision engine** that evaluates match/pass/counter decisions on marginal-wins-per-dollar.
5. A recommended **2026-27 UCLA roster** — 15 players, dollars assigned, starters called, rationale defended.

## The honest framing (read this first)

NIL and rev-share contract values are **largely non-public**. Schools don't disclose player salaries, collectives operate opaquely, and the Deloitte-run NIL Go clearinghouse has only reviewed a fraction of reported deal volume. Every dollar figure in this project is one of:

- **Reported** (sourced to a specific outlet, cited inline),
- **Anchor-comp** (derived from On3 NIL valuations as relative comps),
- **Modeled** (output of the valuation framework below, clearly flagged), or
- **Assumption** (stated explicitly with rationale).

The methodology is the product. Any single dollar output is illustrative.

## Project structure

```
ucla-mbb-revshare-model/
├── docs/                              # Written analysis, one per section
│   ├── 00_introduction.md             # Framing, data limits, reading order
│   ├── 01_budget_allocation.md        # UCLA athletic revenue → MBB budget
│   ├── 02_valuation_framework.md      # Player market-value methodology
│   ├── 03_roster_archetypes.md        # Strategic archetype comparison
│   ├── 04_portal_scenarios.md         # Decision engine with worked examples
│   └── 05_proposed_2026_27_roster.md  # The recommended roster + defense
├── data/
│   ├── raw/
│   │   ├── reported_contracts_2025_26.csv   # Publicly reported deals
│   │   ├── on3_comps_2025_26.csv            # On3 NIL valuation anchors
│   │   └── ucla_roster_2025_26.csv          # UCLA's current roster
│   └── processed/                     # Model outputs, back-test results
├── src/
│   ├── valuation/                     # Player market-value model
│   │   ├── features.py                # Feature engineering
│   │   ├── model.py                   # Core valuation logic
│   │   └── backtest.py                # Validation against known deals
│   ├── budget/
│   │   └── allocator.py               # Top-down budget flow
│   ├── roster/
│   │   ├── archetypes.py              # Stars-and-scrubs / Balanced / Flywheel
│   │   └── constructor.py             # Cap-constrained roster builder
│   └── portal/
│       └── decision_engine.py         # Match/pass/counter framework
├── app/
│   └── streamlit_app.py               # Interactive valuation + budget sandbox
├── notebooks/                         # Exploratory analysis
├── requirements.txt
└── README.md
```

## Getting started

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the valuation back-test
python -m src.valuation.backtest

# Launch the interactive app
streamlit run app/streamlit_app.py
```

## Current status

| Section | Status | Notes |
|---|---|---|
| 01 — Budget allocation | ✅ Written | Uses reported UCLA figures (Jarmond, LA Times, Yahoo) |
| 02 — Valuation framework | ✅ Model works, 🟡 weights need calibration | Back-tested against 5 known 2025-26 deals |
| 03 — Roster archetypes | ✅ Framework + builder | Three archetypes parameterized |
| 04 — Portal scenarios | 🟡 Engine built, scenarios stubbed | Fill in with 2026 portal names as they hit |
| 05 — Proposed 2026-27 roster | 🟡 Template ready | Finalize once portal window opens |
| Streamlit app | 🟡 Working skeleton | Valuation + budget tabs live; roster builder next |

## Key sources

- **House settlement mechanics**: NCAA, Sports Illustrated, Sportico
- **Market benchmarks**: On3 ($932.5M CBB NIL estimate, 2025-26), nil-ncaa.com, The Athletic coaches survey, CBS Sports (Norlander)
- **UCLA-specific reporting**: LA Times (Jarmond interview, June 2025), Yahoo Sports (UCLA FY budget), Daily Bruin
- **Player analytics**: KenPom, Bart Torvik, EvanMiya (not bundled — see `docs/02_valuation_framework.md` for integration notes)

## Who this is for

A UCLA front office hire interview, a portfolio piece for sports analytics roles, or a framework any program's cap manager could fork. Everything is built to be inspected, argued with, and replaced with better data as it becomes available.
