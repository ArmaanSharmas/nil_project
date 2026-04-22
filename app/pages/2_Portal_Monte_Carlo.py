"""
Page 3: Portal Monte Carlo — probability-weighted decision analysis.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.set_page_config(page_title="Portal Monte Carlo", page_icon="🎲", layout="wide")
st.title("Portal Decision — Monte Carlo Analysis")
st.markdown(
    "Every portal input is uncertain. This page runs 5,000 simulations per scenario, "
    "perturbing marginal wins, fit multiplier, opportunity cost, and market price within "
    "realistic bands. The output is a **probability** that MATCH / COUNTER / PASS is correct."
)

from src.portal import (
    PortalScenario, score_scenario, Decision,
    SimulationInputs, monte_carlo_decision,
)

st.subheader("Configure a scenario")

col1, col2 = st.columns(2)
with col1:
    player    = st.text_input("Player", "Rob Wright III (BYU PG)")
    our_val   = st.number_input("Our valuation ($)", 0, 10_000_000, 1_600_000, 50_000)
    mkt_price = st.number_input("Market price ($)", 0, 10_000_000, 2_000_000, 50_000)
    wins      = st.slider("Marginal wins over alt", 0.0, 10.0, 4.0, 0.1)

with col2:
    fit       = st.slider("Fit multiplier", 0.5, 1.5, 1.30, 0.05)
    opp       = st.slider("Opportunity cost index", 0.0, 2.0, 1.50, 0.05)
    n_sims    = st.select_slider("Simulations", [1000, 2500, 5000, 10000], value=5000)

st.subheader("Uncertainty bands")
col3, col4 = st.columns(2)
with col3:
    wins_spread = st.slider("Wins uncertainty (±)", 0.0, 3.0, 1.5, 0.1)
    fit_spread  = st.slider("Fit uncertainty (±)", 0.0, 0.30, 0.12, 0.01)
with col4:
    opp_spread  = st.slider("Opp-cost uncertainty (±)", 0.0, 0.60, 0.30, 0.05)
    price_spread = st.slider("Market price uncertainty (%)", 0.0, 0.30, 0.15, 0.01)

scenario = PortalScenario(
    scenario_id="ui_scenario",
    player=player,
    context="User-defined",
    our_valuation_usd=int(our_val),
    market_price_usd=int(mkt_price),
    marginal_wins=wins,
    fit_multiplier=fit,
    opportunity_cost_index=opp,
)
sim_cfg = SimulationInputs(
    wins_spread=wins_spread,
    fit_spread=fit_spread,
    opp_cost_spread=opp_spread,
    price_spread_pct=price_spread,
)

if st.button("Run Monte Carlo", type="primary"):
    with st.spinner(f"Running {n_sims:,} simulations…"):
        mc = monte_carlo_decision(scenario, inputs=sim_cfg, n_sims=n_sims, seed=None)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P(MATCH)",   f"{mc.prob_match:.1%}")
    c2.metric("P(COUNTER)", f"{mc.prob_counter:.1%}")
    c3.metric("P(PASS)",    f"{mc.prob_pass:.1%}")
    c4.metric("Modal decision", mc.modal_decision.value)

    st.subheader("Score distribution (5th / 50th / 95th percentile)")
    import plotly.figure_factory as ff
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=mc.raw_scores, nbinsx=60,
        marker_color="#2774AE", opacity=0.75,
        name="Score distribution",
    ))
    fig.add_vline(x=2.0,  line_dash="dash", line_color="green",  annotation_text="MATCH threshold (2.0)")
    fig.add_vline(x=0.8,  line_dash="dash", line_color="orange", annotation_text="COUNTER threshold (0.8)")
    fig.add_vline(x=mc.score_p50, line_dash="solid", line_color="#003B5C", annotation_text=f"P50={mc.score_p50:.2f}")
    fig.update_layout(
        title=f"Decision score distribution — {player}",
        xaxis_title="Decision score",
        yaxis_title="Simulations",
        template="simple_white",
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    if mc.prob_match > 0.60:
        st.success(f"HIGH CONFIDENCE MATCH ({mc.prob_match:.1%} of sims)")
    elif mc.prob_pass > 0.60:
        st.error(f"HIGH CONFIDENCE PASS ({mc.prob_pass:.1%} of sims)")
    elif max(mc.prob_match, mc.prob_counter, mc.prob_pass) < 0.50:
        st.warning("LOW CONFIDENCE — genuinely ambiguous. Improve your win/fit estimates before deciding.")
    else:
        st.info(f"MODERATE CONFIDENCE — lean {mc.modal_decision.value}. P50 score = {mc.score_p50:.2f}")
else:
    st.info("Set inputs above and click **Run Monte Carlo** to see probability distributions.")
