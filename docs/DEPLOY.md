# Deployment Guide

## Local development

```bash
git clone <repo>
cd ucla-mbb-revshare-model

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Verify everything works
python -m tests.test_smoke          # all smoke tests
python -m src.valuation.backtest    # MAE 10.7% confirmed
python -m src.portal.monte_carlo    # 6 real 2026 scenarios

# Launch the app
streamlit run app/streamlit_app.py
```

App runs at `http://localhost:8501`.

## Streamlit Community Cloud (free hosting)

1. Push repo to GitHub (public or private with Community Cloud access)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Set:
   - **Repository:** your-username/ucla-mbb-revshare-model
   - **Branch:** main
   - **Main file path:** `app/streamlit_app.py`
4. Click Deploy

The multi-page app structure (`app/pages/`) is detected automatically by Streamlit.

### Dependencies note

`pulp` is in `requirements.txt` — Streamlit Cloud installs it automatically.
No external API keys required; no secrets needed for the base app.

## Running the CLI tools

```bash
# Budget allocation
python -m src.budget.allocator

# Back-test the valuation model
python -m src.valuation.backtest

# Portal decision engine (deterministic)
python -m src.portal.decision_engine

# Monte Carlo confidence (5,000 sims per scenario)
python -m src.portal.monte_carlo

# ILP vs Greedy comparison
python -m src.roster.ilp_constructor

# Archetype comparison at any budget
python -m src.roster.archetypes   # default $6.2M

# Run all tests
pytest tests/
```

## Adding real 2026 portal players

1. Open `data/raw/portal_scenarios.csv`
2. Add a row with the player's stats, your valuation, market price estimate, and fit inputs
3. Re-run `python -m src.portal.monte_carlo` to get updated probability distributions
4. Update `docs/05_proposed_2026_27_roster.md` with the result

## Adding a new season's back-test data

1. Pull end-of-season stats from Bart Torvik (`barttorvik.com`) or EvanMiya
2. Update `production_score` values in `src/valuation/backtest.py → BACKTEST_INPUTS`
3. Add confirmed contracts to `data/raw/reported_contracts_2025_26.csv`
4. Update On3 NIL valuations in `data/raw/on3_comps_2025_26.csv`
5. Run `python -m src.valuation.backtest` and review new MAE
6. If MAE increases significantly, check for systematic bias in a new eligibility class
   or position category — follow the CHANGELOG.md pattern for documenting fixes
