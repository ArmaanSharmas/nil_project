"""
Page 4: Interactive Roster Builder — ILP optimizer with positional constraints.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.set_page_config(page_title="Roster Builder", page_icon="🏗", layout="wide")
st.title("Cap-Constrained Roster Builder")
st.markdown(
    "Add candidates to a pool and the ILP optimizer finds the optimal 15-man roster "
    "within your budget. Uses the same archetype slot distributions from Section 3."
)

from src.roster import (
    all_archetypes, balanced_veteran,
    build_roster_from_archetype,
)
from src.roster.constructor import CandidatePlayer
from src.roster.ilp_constructor import build_roster_ilp, PositionalConstraints

# ---------- Session state: candidate pool ----------
if "candidates" not in st.session_state:
    st.session_state.candidates = [
        CandidatePlayer("Rob Wright III (portal target)", "PG", "Starter", 1_600_000, 1_800_000),
        CandidatePlayer("Tyler Bilodeau (returner)",      "PF", "Starter", 1_200_000, 1_100_000, is_returner=True),
        CandidatePlayer("Xavier Booker (returner)",       "C",  "Starter",   900_000,   800_000, is_returner=True),
        CandidatePlayer("Eric Dailey Jr. (returner)",     "SF", "Starter",   850_000,   750_000, is_returner=True),
        CandidatePlayer("Brandon Williams (returner)",    "SG", "Rotation",  450_000,   420_000, is_returner=True),
        CandidatePlayer("Portal SG target",               "SG", "Starter",   700_000,   600_000),
        CandidatePlayer("Portal wing",                    "SF", "Rotation",  400_000,   350_000),
        CandidatePlayer("Eric Freeny (returner)",         "PG", "Rotation",  220_000,   200_000, is_returner=True),
        CandidatePlayer("Portal C depth",                 "C",  "Rotation",  200_000,   180_000),
        CandidatePlayer("FR signee PG",                   "PG", "Developmental", 160_000, 140_000),
        CandidatePlayer("FR signee SF",                   "SF", "Developmental", 145_000, 125_000),
        CandidatePlayer("FR signee PF",                   "PF", "Developmental", 130_000, 110_000),
        CandidatePlayer("Lino Mark (returner)",           "PG", "Developmental", 120_000, 100_000, is_returner=True),
        CandidatePlayer("Walk-on+",                       "PF", "Developmental",  80_000,  65_000),
        CandidatePlayer("Redshirt C",                     "C",  "Developmental",  90_000,  75_000),
    ]

# ---------- Sidebar: add a player ----------
with st.sidebar:
    st.header("Add candidate player")
    p_name   = st.text_input("Name", "New Portal Target")
    p_pos    = st.selectbox("Position", ["PG","SG","SF","PF","C"])
    p_role   = st.selectbox("Role", ["Starter","Rotation","Developmental"])
    p_val    = st.number_input("Estimated value ($)", 0, 5_000_000, 800_000, 50_000)
    p_price  = st.number_input("Market price ($)",    0, 5_000_000, 900_000, 50_000)
    p_ret    = st.checkbox("Returner?")
    if st.button("Add to pool"):
        st.session_state.candidates.append(
            CandidatePlayer(p_name, p_pos, p_role, p_val, p_price, is_returner=p_ret)
        )
        st.success(f"Added {p_name}")

    st.divider()
    if st.button("Reset to default UCLA pool"):
        del st.session_state["candidates"]
        st.rerun()

# ---------- Main: build the roster ----------
col1, col2 = st.columns([1, 2])
with col1:
    arch_name = st.selectbox(
        "Archetype",
        [a.name for a in all_archetypes()],
        index=1,  # Balanced Veteran default
    )
    budget = st.number_input("Total budget ($)", 1_000_000, 20_000_000, 6_200_000, 100_000)
    method = st.radio("Optimizer", ["ILP (optimal)", "Greedy (fast)"], index=0)
    max_pg = st.slider("Max PGs on roster", 1, 5, 3)
    max_c  = st.slider("Max Cs on roster",  1, 4, 3)

arch = next(a for a in all_archetypes() if a.name == arch_name)
candidates = st.session_state.candidates

if method == "ILP (optimal)":
    pc = PositionalConstraints(max_per_position={"PG": max_pg, "C": max_c})
    roster = build_roster_ilp(arch, budget, candidates, pos_constraints=pc)
else:
    roster = build_roster_from_archetype(arch, budget, candidates)

with col2:
    st.subheader(f"Optimised roster — {roster.archetype_name}")
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total cost",    f"${roster.total_cost:,}")
    mc2.metric("Under budget",  f"${roster.under_budget_by:,}")
    mc3.metric("Slots filled",  len(roster.slots))

    if roster.slots:
        import pandas as pd
        rows = []
        for s in sorted(roster.slots, key=lambda x: -x.actual_cost):
            rows.append({
                "Player": s.player_name,
                "Pos":    s.position,
                "Role":   s.projected_role,
                "Slot budget": f"${s.slot_budget:,}",
                "Actual cost": f"${s.actual_cost:,}",
                "Δ from slot":  f"${s.variance_from_slot:+,}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("No feasible roster found. Try increasing budget or relaxing positional constraints.")

st.subheader("Candidate pool")
import pandas as pd
pool_rows = [
    {"Name": c.name, "Pos": c.position, "Role": c.projected_role,
     "Est. value": f"${c.estimated_value:,}", "Market price": f"${c.market_price:,}",
     "Value/$": f"{c.value_per_dollar:.2f}", "Returner": "✓" if c.is_returner else ""}
    for c in candidates
]
st.dataframe(pd.DataFrame(pool_rows), use_container_width=True, hide_index=True)
