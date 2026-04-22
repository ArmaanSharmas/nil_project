"""
UCLA MBB Rev-Share Model — redesigned dark-theme Streamlit app.

Run with:
    PYTHONPATH=. streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root so src/ imports resolve regardless of working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
import plotly.graph_objects as go

try:
    from src.valuation import PlayerFeatures, Position, EligibilityClass, value_player
    from src.valuation.features import PortalDemandSignal, OffCourtSignal
    from src.portal import PortalScenario, score_scenario
    from src.portal.monte_carlo import monte_carlo_decision
    _IMPORTS_OK = True
except Exception as _import_err:
    _IMPORTS_OK = False
    _IMPORT_MSG = str(_import_err)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UCLA MBB Rev-Share Model",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Chrome ── */
#MainMenu  { visibility: hidden; }
footer     { visibility: hidden; }
header     { visibility: hidden; }

/* ── Page background ── */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: #0a0e1a !important;
}
[data-testid="stSidebar"] { background-color: #111827; }

/* ── Typography ── */
body, p, li, .stMarkdown, .stText, div, span {
    color: #9aa5b4;
    font-family: "Inter", "Segoe UI", sans-serif;
}
h1 { color: #FFB300 !important; margin-bottom: 0 !important; }
h2, h3, h4 { color: #ffffff !important; }
label, .stSelectbox label, .stCheckbox label { color: #9aa5b4 !important; }

/* ── Tab bar ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #111827;
    border-radius: 12px;
    gap: 4px;
    padding: 4px;
    border: 1px solid #1f2937;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #9aa5b4 !important;
    background-color: transparent;
    font-weight: 500;
    padding: 6px 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #2774AE !important;
    color: #ffffff !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem;
}

/* ── Metric containers ── */
[data-testid="metric-container"] {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricValue"]  { color: #FFB300 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"]  { color: #6b7280 !important; }
[data-testid="stMetricDelta"]  { color: #10b981 !important; }

/* ── Select / input boxes ── */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput [data-baseweb="input"] {
    background-color: #111827 !important;
    border-color: #1f2937 !important;
    color: #9aa5b4 !important;
}

/* ── Checkboxes ── */
.stCheckbox span { color: #9aa5b4 !important; }

/* ── Divider ── */
hr { border-color: #1f2937 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

if not _IMPORTS_OK:
    st.error(f"Import error — make sure you run with `PYTHONPATH=. streamlit run app/streamlit_app.py`\n\nDetail: {_IMPORT_MSG}")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
CHART_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#9aa5b4", size=12),
)

def card(body_html: str, extra_style: str = "") -> None:
    st.markdown(
        f'<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;'
        f'padding:1.4rem;{extra_style}">{body_html}</div>',
        unsafe_allow_html=True,
    )

def gold(text: str) -> str:
    return f'<span style="color:#FFB300;font-weight:700;">{text}</span>'

def muted(text: str) -> str:
    return f'<span style="color:#6b7280;">{text}</span>'

def badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;font-size:11px;font-weight:700;'
        f'padding:2px 9px;border-radius:20px;letter-spacing:0.05em;">{label}</span>'
    )

def progress_bar(value: int, max_val: int = 5_000_000) -> str:
    pct = min(100.0, value / max_val * 100)
    return (
        f'<div style="background:#1f2937;border-radius:4px;height:8px;margin:10px 0 4px 0;">'
        f'<div style="background:#FFB300;border-radius:4px;height:8px;width:{pct:.1f}%;"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;">'
        f'<span>$0</span><span>$5M</span></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:1.5rem;">
  <div style="background:#2774AE;border-radius:14px;width:52px;height:52px;
              display:flex;align-items:center;justify-content:center;font-size:26px;
              flex-shrink:0;">🏀</div>
  <div>
    <h1 style="margin:0;font-size:1.8rem;">UCLA Men's Basketball</h1>
    <p style="margin:0;color:#6b7280;font-size:0.9rem;">
      Rev-Share &amp; Roster Construction Model &nbsp;·&nbsp; 2026-27
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_budget, tab_value, tab_portal, tab_roster, tab_contracts = st.tabs(
    ["📊 Budget", "💰 Player Value", "🔀 Portal Decisions", "📋 Proposed Roster", "📝 Contract Strategy"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BUDGET
# ══════════════════════════════════════════════════════════════════════════════
with tab_budget:
    # ── Top metric cards ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("2026-27 Rev-Share Cap", "$21.3M")
    m2.metric("MBB Allocation (15%)", "$3.2M")
    m3.metric("Third-Party NIL (est.)", "$3.0M")
    m4.metric("Total MBB Budget", "$6.2M")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Donut chart ───────────────────────────────────────────────────────────
    with col_left:
        st.markdown("#### Revenue-Share Allocation — $21.3M")
        CAP = 21_320_000
        donut = go.Figure(go.Pie(
            labels=["Football", "Men's Basketball", "Women's Basketball", "Olympic / Other"],
            values=[CAP * 0.75, CAP * 0.15, CAP * 0.05, CAP * 0.05],
            hole=0.58,
            marker_colors=["#2774AE", "#FFB300", "#10b981", "#6b7280"],
            textinfo="label+percent",
            textfont=dict(color="#ffffff", size=12),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        donut.update_layout(
            **CHART_DEFAULTS,
            showlegend=False,
            height=300,
            margin=dict(l=0, r=0, t=32, b=0),
            annotations=[dict(
                text="$21.3M",
                x=0.5, y=0.5,
                font=dict(size=20, color="#FFB300", family="Inter"),
                showarrow=False,
            )],
        )
        st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})

    # ── Peer comparison bar chart ─────────────────────────────────────────────
    with col_right:
        st.markdown("#### Program Budget Comparison")
        programs = ["Kentucky", "BYU", "Duke", "P4 Average", "UCLA (high)", "UCLA (base)"]
        budgets  = [22.0,       13.0,  12.0,  8.5,          7.7,           6.2          ]
        bar_colors = [
            "#6b7280", "#6b7280", "#6b7280", "#6b7280",
            "#2774AE", "#FFB300",
        ]
        bar_fig = go.Figure(go.Bar(
            y=programs,
            x=budgets,
            orientation="h",
            marker_color=bar_colors,
            text=[f"${v}M" for v in budgets],
            textposition="outside",
            textfont=dict(color="#9aa5b4", size=11),
            hovertemplate="<b>%{y}</b>: $%{x}M<extra></extra>",
        ))
        bar_fig.update_layout(
            **CHART_DEFAULTS,
            height=300,
            margin=dict(l=0, r=40, t=32, b=0),
            xaxis=dict(
                showgrid=True, gridcolor="#1f2937",
                tickfont=dict(color="#9aa5b4"),
                tickprefix="$", ticksuffix="M",
                range=[0, 26],
            ),
            yaxis=dict(tickfont=dict(color="#9aa5b4"), autorange="reversed"),
        )
        st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Analyst note ─────────────────────────────────────────────────────────
    card(
        '<p style="margin:0;font-size:1rem;line-height:1.7;color:#9aa5b4;">'
        "<b style='color:#ffffff;'>UCLA isn't Kentucky.</b> A $6.2M budget puts them at "
        "the Power Four median — enough to compete, not enough to buy a superstar-heavy "
        "roster. The edge has to come from <b style='color:#FFB300;'>construction</b>, "
        "not spending."
        "</p>",
        extra_style="border-left:3px solid #2774AE;",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLAYER VALUE
# ══════════════════════════════════════════════════════════════════════════════
with tab_value:
    PRODUCTION_MAP = {
        "Elite — All-American / lottery track (Boozer, Dybantsa level)": 97,
        "Star — P4 All-Conference starter (Dent, Toppin level)": 90,
        "Solid starter — P4 reliable contributor": 78,
        "Rotation player — 15-25 min/game": 62,
        "Reserve / developmental": 45,
    }
    POSITION_MAP = {
        "Point Guard — PG":    Position.PG,
        "Shooting Guard — SG": Position.SG,
        "Small Forward — SF":  Position.SF,
        "Power Forward — PF":  Position.PF,
        "Center — C":          Position.C,
    }
    ELIG_MAP = {
        "Freshman — FR":    EligibilityClass.FR,
        "Sophomore — SO":   EligibilityClass.SO,
        "Junior — JR":      EligibilityClass.JR,
        "Senior — SR":      EligibilityClass.SR,
        "5th Year — RS-SR": EligibilityClass.RS_SR,
    }
    P4_MAP = {
        "None":        0,
        "1-2 programs": 1,
        "3-4 programs": 3,
        "5+ programs":  5,
    }

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### Player Profile")
        prod_label = st.selectbox("Production level", list(PRODUCTION_MAP.keys()))
        pos_label  = st.selectbox("Position", list(POSITION_MAP.keys()))
        elig_label = st.selectbox("Eligibility class", list(ELIG_MAP.keys()), index=2)
        p4_label   = st.selectbox("P4 programs competing?", list(P4_MAP.keys()))

        st.markdown("<br>", unsafe_allow_html=True)
        la_market   = st.checkbox("LA market / UCLA brand fit bonus")
        nba_premium = st.checkbox("Turned down NBA Draft to return")
        returner    = st.checkbox("Returning starter (same program)")

    with right:
        try:
            production_score = PRODUCTION_MAP[prod_label]
            position         = POSITION_MAP[pos_label]
            elig             = ELIG_MAP[elig_label]
            p4_offers        = P4_MAP[p4_label]

            features = PlayerFeatures(
                name="Hypothetical Player",
                position=position,
                eligibility_class=elig,
                production_score=production_score,
                portal_demand=PortalDemandSignal(p4_offers_count=p4_offers),
                off_court=OffCourtSignal(
                    market_fit_bonus=0.10 if la_market else 0.0,
                ),
                nba_draft_eligible_premium_usd=500_000 if nba_premium else 0,
                proven_p4_returner=returner,
            )
            result = value_player(features)

            # ── Main valuation display ────────────────────────────────────────
            st.markdown(
                f'<div style="text-align:center;padding:1.5rem 0 0.5rem;">'
                f'<div style="color:#6b7280;font-size:0.85rem;letter-spacing:0.08em;'
                f'text-transform:uppercase;">Estimated Market Value</div>'
                f'<div style="color:#FFB300;font-size:3rem;font-weight:800;'
                f'line-height:1.1;margin:6px 0;">${result.point_estimate:,}</div>'
                f'<div style="color:#6b7280;font-size:0.9rem;">'
                f'${result.low_band:,} &nbsp;–&nbsp; ${result.high_band:,} &nbsp;'
                f'<span style="font-size:0.8rem;">(15th–85th %ile)</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(progress_bar(result.point_estimate), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<div style="color:#6b7280;font-size:0.75rem;letter-spacing:0.08em;'
                'text-transform:uppercase;margin-bottom:8px;">Component Breakdown</div>',
                unsafe_allow_html=True,
            )

            def row(label: str, value: str, is_dollar: bool = True) -> str:
                val_str = f"${int(value):,}" if is_dollar and str(value).lstrip("-").isdigit() else value
                return (
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:6px 0;border-bottom:1px solid #1f2937;">'
                    f'<span style="color:#9aa5b4;">{label}</span>'
                    f'<span style="color:#FFB300;font-weight:600;">{val_str}</span>'
                    f'</div>'
                )

            breakdown_html = (
                row("Production tier base", str(result.base_value))
                + row("Position scarcity multiplier", f"{result.position_multiplier:.2f}×", is_dollar=False)
                + row("Eligibility multiplier", f"{result.eligibility_multiplier:.2f}×", is_dollar=False)
                + row("Portal demand multiplier", f"{result.portal_demand_multiplier:.2f}×", is_dollar=False)
                + row("Off-court bump", str(result.off_court_bump))
                + row("On3 anchor delta", str(result.on3_anchor_delta))
                + row("NBA draft-eligible premium", str(result.nba_premium_applied))
                + row("Retention premium", str(result.retention_premium_applied))
            )
            card(breakdown_html)

            conf_color = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}[result.confidence]
            st.markdown(
                f'<div style="margin-top:10px;display:flex;align-items:center;gap:8px;">'
                f'<span style="color:#6b7280;font-size:0.85rem;">Model confidence:</span>'
                f'<span style="color:{conf_color};font-weight:700;">{result.confidence}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if result.notes:
                for note in result.notes:
                    st.warning(note)

        except Exception as e:
            st.error(f"Valuation error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PORTAL EVALUATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_portal:
    st.markdown(
        '<p style="color:#6b7280;margin-top:-8px;">Enter any portal target\'s numbers '
        'and the model runs 2,000 simulations to give you a MATCH / COUNTER / PASS recommendation.</p>',
        unsafe_allow_html=True,
    )

    p_left, p_right = st.columns([1, 1], gap="large")

    with p_left:
        st.markdown("#### Target Profile")
        p_name = st.text_input("Player name (optional)", placeholder="e.g. John Smith")

        st.markdown("#### Financials")
        p_our_val = st.number_input(
            "Our valuation ($)",
            min_value=0, max_value=5_000_000, value=1_200_000, step=50_000,
            help="Use the Player Value tab to estimate this.",
        )
        p_market = st.number_input(
            "Market price — what it'd take to sign ($)",
            min_value=0, max_value=5_000_000, value=1_500_000, step=50_000,
        )

        st.markdown("#### Decision Inputs")
        p_wins = st.slider(
            "Marginal wins above your best alternative",
            min_value=0.0, max_value=8.0, value=3.0, step=0.1,
            help="How many extra wins does this player produce vs. who you'd sign instead?",
        )
        p_fit = st.slider(
            "Fit multiplier (0.7 = poor fit · 1.0 = neutral · 1.3 = ideal)",
            min_value=0.7, max_value=1.3, value=1.0, step=0.05,
            help="System fit, positional need, culture. UCLA-specific factors.",
        )
        p_opp = st.slider(
            "Opportunity cost (0 = no cost · 2 = high cost)",
            min_value=0.0, max_value=2.0, value=1.2, step=0.1,
            help="How much does committing this money hurt other roster decisions?",
        )

    with p_right:
        try:
            if p_market <= 0:
                st.info("Set a market price to see the evaluation.")
            else:
                scenario = PortalScenario(
                    scenario_id="live",
                    player=p_name or "Target Player",
                    context="Live evaluation",
                    our_valuation_usd=int(p_our_val),
                    market_price_usd=int(p_market),
                    marginal_wins=p_wins,
                    fit_multiplier=p_fit,
                    opportunity_cost_index=p_opp,
                )
                det = score_scenario(scenario)
                mc  = monte_carlo_decision(scenario, n_sims=2000, seed=42)

                D_COLOR = {"MATCH": "#10b981", "COUNTER": "#f59e0b", "PASS": "#ef4444"}
                D_ICON  = {"MATCH": "✓", "COUNTER": "⚡", "PASS": "✕"}
                dv      = det.decision.value
                dc      = D_COLOR[dv]

                # ── Big decision badge ────────────────────────────────────────
                st.markdown(
                    f'<div style="text-align:center;padding:1.4rem 0 0.8rem;">'
                    f'<div style="display:inline-block;background:{dc}22;border:2px solid {dc};'
                    f'border-radius:16px;padding:0.6rem 2.2rem;">'
                    f'<span style="color:{dc};font-size:2rem;font-weight:800;">'
                    f'{D_ICON[dv]} {dv}</span>'
                    f'</div>'
                    f'<div style="color:#6b7280;font-size:0.8rem;margin-top:8px;">'
                    f'Decision score: <span style="color:#ffffff;font-weight:600;">'
                    f'{det.score:.2f}</span>'
                    f'&nbsp;·&nbsp;Overpay: '
                    f'<span style="color:{"#ef4444" if scenario.overpay_ratio > 1.3 else "#9aa5b4"};'
                    f'font-weight:600;">{scenario.overpay_ratio:.2f}×</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                # ── Monte Carlo probability chart ─────────────────────────────
                st.markdown("#### Simulation probabilities (n=2,000)")
                mc_fig = go.Figure(go.Bar(
                    x=[mc.prob_match, mc.prob_counter, mc.prob_pass],
                    y=["MATCH", "COUNTER", "PASS"],
                    orientation="h",
                    marker_color=["#10b981", "#f59e0b", "#ef4444"],
                    text=[f"{mc.prob_match:.0%}", f"{mc.prob_counter:.0%}", f"{mc.prob_pass:.0%}"],
                    textposition="outside",
                    textfont=dict(color="#9aa5b4", size=12),
                    hovertemplate="%{y}: %{x:.1%}<extra></extra>",
                ))
                mc_fig.update_layout(
                    **CHART_DEFAULTS,
                    height=150,
                    margin=dict(l=0, r=50, t=8, b=0),
                    xaxis=dict(
                        range=[0, 1], tickformat=".0%",
                        tickfont=dict(color="#9aa5b4", size=10),
                        showgrid=False,
                    ),
                    yaxis=dict(tickfont=dict(color="#9aa5b4", size=12)),
                    bargap=0.35,
                )
                st.plotly_chart(mc_fig, use_container_width=True, config={"displayModeBar": False})

                # ── Score distribution ────────────────────────────────────────
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Score P10", f"{mc.score_p10:.2f}")
                sc2.metric("Score P50", f"{mc.score_p50:.2f}")
                sc3.metric("Score P90", f"{mc.score_p90:.2f}")

                # ── Rationale ─────────────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                card(
                    f'<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;'
                    f'letter-spacing:.07em;margin-bottom:6px;">Model Rationale</div>'
                    f'<div style="color:#9aa5b4;line-height:1.7;">{det.rationale}</div>',
                    extra_style=f"border-left:3px solid {dc};",
                )

        except Exception as e:
            st.error(f"Evaluation error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How to use guide ──────────────────────────────────────────────────────
    with st.expander("How to use this tool"):
        st.markdown("""
**Step 1 — Get a valuation.** Use the Player Value tab to estimate what the player is worth to UCLA.
Paste that number into "Our valuation."

**Step 2 — Find a market price.** Check On3, 247Sports, or reported offers. This is what it'd
actually take to sign them, not what you think they're worth.

**Step 3 — Estimate marginal wins.** How many extra wins does this player add over whoever you'd
sign if they said no? A true starter-level upgrade is ~2.5–4.0 wins. Depth adds ~0.5–1.5.

**Step 4 — Set fit and opportunity cost.** Fit above 1.1 means they fill a genuine positional need
in your system. Opportunity cost above 1.5 means committing this money significantly limits other moves.

**Reading the result:**
- **MATCH** (score > 2.0) — the wins-per-dollar math works even after opportunity cost.
- **COUNTER** (0.8–2.0) — positive value but don't overpay. Offer your valuation, not their ask.
- **PASS** (< 0.8) — the math doesn't work. Reallocate budget elsewhere.
        """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CAP SHEET BUILDER
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROPOSED ROSTER
# ══════════════════════════════════════════════════════════════════════════════
with tab_roster:
    CAP = 6_200_000
    N_SLOTS = 15

    POS_OPTIONS   = ["—", "PG", "SG", "SF", "PF", "C"]
    ROLE_OPTIONS  = ["—", "Starter", "Rotation", "Development"]
    SOURCE_OPTIONS = ["—", "Returning", "Portal", "Recruit"]

    POS_COLORS = {"PG": "#2774AE", "SG": "#2774AE", "SF": "#FFB300", "PF": "#FFB300", "C": "#10b981"}
    SOURCE_STYLES = {
        "Portal":    ("background:#1d4ed8;color:#93c5fd;", "PORTAL"),
        "Recruit":   ("background:#065f46;color:#6ee7b7;", "RECRUIT"),
        "Returning": ("background:#1f2937;color:#9aa5b4;", "RET"),
    }

    st.markdown(
        '<p style="color:#6b7280;margin-top:-8px;">Build your roster slot by slot. '
        'Totals and the cap bar update live as you type.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    cs_left, cs_right = st.columns([3, 2], gap="large")

    # ── Input grid ────────────────────────────────────────────────────────────
    with cs_left:
        hc1, hc2, hc3, hc4, hc5 = st.columns([2.8, 1, 1.2, 1.4, 1])
        hc1.markdown('<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;padding-bottom:4px;">Player</div>', unsafe_allow_html=True)
        hc2.markdown('<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;padding-bottom:4px;">Pos</div>', unsafe_allow_html=True)
        hc3.markdown('<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;padding-bottom:4px;">Role</div>', unsafe_allow_html=True)
        hc4.markdown('<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;padding-bottom:4px;">Salary ($)</div>', unsafe_allow_html=True)
        hc5.markdown('<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;letter-spacing:.07em;padding-bottom:4px;">Source</div>', unsafe_allow_html=True)

        slots: list[dict] = []
        for i in range(1, N_SLOTS + 1):
            c1, c2, c3, c4, c5 = st.columns([2.8, 1, 1.2, 1.4, 1])
            with c1:
                name = st.text_input(
                    f"#{i}", placeholder=f"Slot {i}",
                    key=f"cs_name_{i}", label_visibility="collapsed",
                )
            with c2:
                pos = st.selectbox(
                    f"pos_{i}", POS_OPTIONS,
                    key=f"cs_pos_{i}", label_visibility="collapsed",
                )
            with c3:
                role = st.selectbox(
                    f"role_{i}", ROLE_OPTIONS,
                    key=f"cs_role_{i}", label_visibility="collapsed",
                )
            with c4:
                salary = st.number_input(
                    f"sal_{i}", min_value=0, max_value=5_000_000,
                    value=0, step=10_000,
                    key=f"cs_sal_{i}", label_visibility="collapsed",
                )
            with c5:
                source = st.selectbox(
                    f"src_{i}", SOURCE_OPTIONS,
                    key=f"cs_src_{i}", label_visibility="collapsed",
                )
            slots.append({"slot": i, "name": name, "pos": pos, "role": role,
                          "salary": salary, "source": source})

    # ── Live summary sidebar ───────────────────────────────────────────────────
    with cs_right:
        filled   = [s for s in slots if s["name"].strip()]
        total    = sum(s["salary"] for s in slots)
        remaining = CAP - total
        pct_used  = min(total / CAP, 1.0) if CAP > 0 else 0

        bar_color = "#ef4444" if total > CAP else "#2774AE"
        bar_pct   = pct_used * 100

        st.markdown("#### Cap Summary")
        card(
            f'<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;'
            f'letter-spacing:.07em;margin-bottom:10px;">Payroll vs $6.2M Cap</div>'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            f'<span style="color:#FFB300;font-size:1.4rem;font-weight:800;">${total:,}</span>'
            f'<span style="color:{"#ef4444" if total > CAP else "#10b981"};font-weight:700;">'
            f'{"OVER" if total > CAP else "UNDER"} by ${abs(remaining):,}</span>'
            f'</div>'
            f'<div style="background:#1f2937;border-radius:4px;height:10px;">'
            f'<div style="background:{bar_color};border-radius:4px;height:10px;'
            f'width:{bar_pct:.1f}%;transition:width 0.3s;"></div>'
            f'</div>'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.75rem;color:#6b7280;margin-top:4px;">'
            f'<span>$0</span><span>Cap: $6.2M</span></div>',
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Slot breakdown ────────────────────────────────────────────────────
        filled_count  = len(filled)
        starter_count = sum(1 for s in slots if s["role"] == "Starter")
        portal_count  = sum(1 for s in slots if s["source"] == "Portal")

        m1, m2, m3 = st.columns(3)
        m1.metric("Slots filled", f"{filled_count}/15")
        m2.metric("Starters",     starter_count)
        m3.metric("Portal",       portal_count)

        # ── Budget by role pie ────────────────────────────────────────────────
        role_totals: dict[str, int] = {}
        for s in slots:
            if s["role"] != "—" and s["salary"] > 0:
                role_totals[s["role"]] = role_totals.get(s["role"], 0) + s["salary"]

        if role_totals:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Budget by Role")
            pie_fig = go.Figure(go.Pie(
                labels=list(role_totals.keys()),
                values=list(role_totals.values()),
                hole=0.50,
                marker_colors=["#2774AE", "#FFB300", "#6b7280"],
                textinfo="label+percent",
                textfont=dict(color="#ffffff", size=12),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
            ))
            pie_fig.update_layout(
                **CHART_DEFAULTS, height=200, showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})

        # ── Position count bar ────────────────────────────────────────────────
        pos_counts: dict[str, int] = {}
        for s in slots:
            if s["pos"] != "—":
                pos_counts[s["pos"]] = pos_counts.get(s["pos"], 0) + 1

        if pos_counts:
            st.markdown("#### Roster by Position")
            pos_fig = go.Figure(go.Bar(
                x=list(pos_counts.keys()),
                y=list(pos_counts.values()),
                marker_color=["#2774AE", "#2774AE", "#FFB300", "#FFB300", "#10b981"],
                text=list(pos_counts.values()),
                textposition="outside",
                textfont=dict(color="#9aa5b4", size=12),
            ))
            pos_fig.update_layout(
                **CHART_DEFAULTS, height=160,
                margin=dict(l=0, r=0, t=8, b=0),
                xaxis=dict(tickfont=dict(color="#9aa5b4")),
                yaxis=dict(
                    tickfont=dict(color="#9aa5b4"),
                    showgrid=True, gridcolor="#1f2937",
                    dtick=1,
                ),
                bargap=0.3,
            )
            st.plotly_chart(pos_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Roster preview table ──────────────────────────────────────────────────
    filled_slots = [s for s in slots if s["name"].strip() or s["salary"] > 0]
    if filled_slots:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Roster Preview")
        tbl = (
            '<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;'
            'letter-spacing:0.07em;border-bottom:1px solid #1f2937;">'
            '<th style="padding:6px 4px;text-align:left;width:28px;">#</th>'
            '<th style="padding:6px 8px;text-align:left;">Player</th>'
            '<th style="padding:6px 4px;text-align:center;">Pos</th>'
            '<th style="padding:6px 8px;text-align:left;">Role</th>'
            '<th style="padding:6px 4px;text-align:right;">Salary</th>'
            '</tr></thead><tbody>'
        )
        for s in filled_slots:
            pc   = POS_COLORS.get(s["pos"], "#9aa5b4")
            rc   = {"Starter": "#ffffff", "Rotation": "#9aa5b4", "Development": "#6b7280"}.get(s["role"], "#6b7280")
            bg   = "#131e2e" if s["slot"] % 2 == 0 else "transparent"
            tag  = ""
            if s["source"] in SOURCE_STYLES:
                sty, lbl = SOURCE_STYLES[s["source"]]
                tag = (f' <span style="{sty}font-size:10px;font-weight:700;padding:1px 7px;'
                       f'border-radius:10px;vertical-align:middle;">{lbl}</span>')
            display_name = s["name"] or f"Slot {s['slot']}"
            display_pos  = s["pos"] if s["pos"] != "—" else "—"
            display_role = s["role"] if s["role"] != "—" else "—"
            sal_str      = f"${s['salary']:,}" if s["salary"] > 0 else "—"
            tbl += (
                f'<tr style="background:{bg};border-bottom:1px solid #1a2535;">'
                f'<td style="padding:7px 4px;color:#6b7280;font-size:0.82rem;">{s["slot"]}</td>'
                f'<td style="padding:7px 8px;color:#e2e8f0;font-size:0.88rem;">{display_name}{tag}</td>'
                f'<td style="padding:7px 4px;text-align:center;'
                f'color:{pc};font-weight:700;font-size:0.82rem;">{display_pos}</td>'
                f'<td style="padding:7px 8px;color:{rc};font-size:0.82rem;">{display_role}</td>'
                f'<td style="padding:7px 4px;text-align:right;color:#FFB300;'
                f'font-weight:600;font-size:0.88rem;">{sal_str}</td>'
                f'</tr>'
            )
        tbl += "</tbody></table>"
        card(tbl, extra_style="padding:1rem;")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CONTRACT STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
with tab_contracts:
    REC_COLORS = {
        "Ideal":       "#10b981",
        "Good":        "#2774AE",
        "Situational": "#f59e0b",
        "Avoid":       "#ef4444",
    }

    st.markdown(
        '<p style="color:#6b7280;margin-top:-8px;">NIL contract structure is one of the '
        'few levers a mid-budget program can actually pull. The teams that figure out '
        '<em>how</em> to structure deals — not just how much to spend — are the ones '
        'that build durable rosters on constrained budgets.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Opening thesis ────────────────────────────────────────────────────────
    card(
        '<p style="margin:0;font-size:1rem;line-height:1.8;color:#9aa5b4;">'
        '<b style="color:#ffffff;">Most programs treat every NIL deal the same way: '
        'one year, flat rate, repeat annually.</b> '
        'That default works fine when you have unlimited budget — you can just outbid '
        'whoever poaches your players. But at $6.2M, you can\'t afford to re-sign '
        'a developed rotation player at open-market prices every summer. '
        'The edge is in <b style="color:#FFB300;">contract structure</b>: '
        'locking in the right players at the right duration before the market prices '
        'them away from you.'
        '</p>',
        extra_style="border-left:3px solid #2774AE;",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 1: The Three Contract Structures ──────────────────────────────
    st.markdown("#### The Three Contract Structures")
    st.markdown(
        '<p style="color:#6b7280;font-size:0.85rem;margin-top:-6px;">'
        'Each structure carries a different risk profile and strategic purpose. '
        'The best programs mix all three depending on player tier and roster stage.</p>',
        unsafe_allow_html=True,
    )

    cs1, cs2, cs3 = st.columns(3, gap="medium")

    cs1.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;'
        'padding:1.4rem;height:100%;">'
        '<div style="color:#2774AE;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Flat One-Year Deal</div>'
        '<div style="color:#ffffff;font-size:1rem;font-weight:700;margin-bottom:10px;">'
        'Maximum Flexibility</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'The current default for most programs. Player gets paid a set amount for one season '
        'with no future commitment on either side. Simple to negotiate, easy to budget, '
        'and leaves full optionality for both parties going into the next portal window.'
        '<br><br>'
        '<b style="color:#fff;">Best for:</b> Stars with uncertain NBA timelines, '
        'senior-year contributors, and portal additions you haven\'t fully evaluated yet.'
        '<br><br>'
        '<b style="color:#f59e0b;">The risk:</b> Every offseason becomes a re-signing '
        'auction. Developmental players you invested in get re-priced at their new '
        'market rate — which you just helped create.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    cs2.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;'
        'padding:1.4rem;height:100%;">'
        '<div style="color:#FFB300;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Multi-Year with Escalators</div>'
        '<div style="color:#ffffff;font-size:1rem;font-weight:700;margin-bottom:10px;">'
        'The Continuity Play</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'Lock in a player for 2–3 years with a guaranteed base that steps up annually '
        '(typically 8–12% per year). The player gets security and a pay raise; '
        'you get a known cost and roster continuity. Both sides are betting on '
        'development — just in opposite directions.'
        '<br><br>'
        '<b style="color:#fff;">Best for:</b> Solid starters you want to build around, '
        'and developmental players before they break out. The earlier you sign, '
        'the bigger the discount versus future open-market rates.'
        '<br><br>'
        '<b style="color:#f59e0b;">The risk:</b> A player who underperforms or '
        'gets injured becomes a cap anchor. Duration creates optionality for them, '
        'not for you — they can still leave; you still owe the money.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    cs3.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;'
        'padding:1.4rem;height:100%;">'
        '<div style="color:#10b981;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Incentive-Laden</div>'
        '<div style="color:#ffffff;font-size:1rem;font-weight:700;margin-bottom:10px;">'
        'Shared Upside</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'Lower guaranteed base paired with performance bonuses: stat thresholds, '
        'minutes floors, All-Conference honors, tournament milestones. '
        'Aligns the player\'s financial incentive with the outcomes you actually need. '
        'Defers cost to the seasons when production — and usually revenue — are highest.'
        '<br><br>'
        '<b style="color:#fff;">Best for:</b> Players you believe in but can\'t fully '
        'value yet, role players whose impact is hard to isolate, and any deal where '
        'you want to share the upside risk rather than absorb it entirely.'
        '<br><br>'
        '<b style="color:#f59e0b;">The risk:</b> Players and agents increasingly '
        'prefer guaranteed money. A heavily incentive-laden offer may lose a bidding '
        'war to a smaller-but-certain flat deal from a rival program.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: The Multi-Year Edge ────────────────────────────────────────
    st.markdown("#### The Multi-Year Edge")
    st.markdown(
        '<p style="color:#6b7280;font-size:0.85rem;margin-top:-6px;">'
        'Where the real structural advantage lives — and where it becomes a trap.</p>',
        unsafe_allow_html=True,
    )

    me1, me2 = st.columns([1, 1], gap="large")

    with me1:
        card(
            '<div style="color:#10b981;font-size:0.72rem;text-transform:uppercase;'
            'letter-spacing:.07em;margin-bottom:10px;">The Developmental Flywheel</div>'
            '<p style="color:#9aa5b4;line-height:1.8;margin:0 0 12px 0;">'
            'The highest-leverage multi-year play is locking in <b style="color:#fff;">'
            'developmental players before they break out</b>. A raw freshman or '
            'sophomore who signs a 3-year deal at $100–130K/yr gives the program '
            'cost certainty through their peak eligibility years. '
            'If they develop into a rotation contributor or starter — which good '
            'recruiting and development makes increasingly likely — you\'ve captured '
            'that production at a fraction of the open-market re-signing price.'
            '</p>'
            '<p style="color:#9aa5b4;line-height:1.8;margin:0;">'
            'The asymmetry is what makes this worth doing: '
            '<b style="color:#FFB300;">downside is capped</b> (you paid $130K for '
            'a player who didn\'t develop — not catastrophic at that price), while '
            '<b style="color:#FFB300;">upside is uncapped</b> (you locked in a '
            'future $400K rotation player at $130K, saving three years of re-signing '
            'costs and preventing a rival from poaching them the moment they show promise). '
            'This is the Flywheel archetype: invest in development, own the output.'
            '</p>',
            extra_style="border-left:3px solid #10b981;",
        )

    with me2:
        card(
            '<div style="color:#ef4444;font-size:0.72rem;text-transform:uppercase;'
            'letter-spacing:.07em;margin-bottom:10px;">The Star Contract Trap</div>'
            '<p style="color:#9aa5b4;line-height:1.8;margin:0 0 12px 0;">'
            'Multi-year logic inverts completely when applied to stars. '
            'Elite players — lottery-track talent, All-Conference performers — '
            'carry a much higher annual departure probability: '
            '<b style="color:#fff;">NBA draft decisions, bigger offers from bluebloods, '
            'transfer portal noise</b>. Roughly half of star-level NIL players '
            'at mid-budget programs leave within two years, whether by going pro '
            'or chasing a larger deal elsewhere.'
            '</p>'
            '<p style="color:#9aa5b4;line-height:1.8;margin:0;">'
            'A 3-year commitment to a star at $1.8–2.2M/yr means you could be '
            'paying out $5–6M in guaranteed money for a player who is gone '
            'after Year 1. The cap anchor '
            '<b style="color:#FFB300;">doesn\'t just hurt the current budget — '
            'it kills your ability to reload through the portal</b> '
            'when you need it most. '
            'Short deals on stars protect flexibility. '
            'Their leverage is in their production; yours is in the option to reallocate.'
            '</p>',
            extra_style="border-left:3px solid #ef4444;",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 3: Strategy Matrix ────────────────────────────────────────────
    st.markdown("#### Contract Strategy Matrix")
    st.markdown(
        '<p style="color:#6b7280;font-size:0.85rem;margin-top:-6px;">'
        'Recommended contract structure by player tier and duration. '
        'Green = structural edge. Red = cap risk outweighs the benefit.</p>',
        unsafe_allow_html=True,
    )

    _MATRIX = [
        ("Star",          1, "Good",        "Stars carry high departure risk. Short deals protect cap flexibility if they leave or go pro."),
        ("Star",          2, "Situational",  "Works when NBA trajectory is confirmed 2+ years out. Adds security but limits future reallocation."),
        ("Star",          3, "Avoid",        "3-year commitments risk locking up $5–6M for a player who may leave after Year 1."),
        ("Solid Starter", 1, "Good",         "Maintains flexibility but risks losing them to a bigger offer when the portal reopens."),
        ("Solid Starter", 2, "Ideal",        "The sweet spot. Locks in a known contributor below Year-2 open-market rates with manageable cap exposure."),
        ("Solid Starter", 3, "Situational",  "Makes sense when eligibility and system fit are both proven. Ensures continuity over the rebuild cycle."),
        ("Rotation",      1, "Situational",  "Low cap risk but leaves the slot vulnerable. Good bridge while developmental players mature."),
        ("Rotation",      2, "Good",         "Depth stability at low AAV. Rotation players rarely outpace their salary in 2 years."),
        ("Rotation",      3, "Avoid",        "Cap locked at 15–25 min/game production. Kills flexibility to upgrade or reload mid-cycle."),
        ("Developmental", 1, "Situational",  "Leaves developmental players poachable once they show promise. Acceptable only under budget pressure."),
        ("Developmental", 2, "Good",         "Locks in raw talent before they break out. If 50%+ develop into rotation contributors, NPV beats annual re-signing."),
        ("Developmental", 3, "Ideal",        "The Flywheel strategy. Lock in at $90–150K/yr. Low downside, high upside if development hits."),
    ]

    tiers_order = ["Star", "Solid Starter", "Rotation", "Developmental"]
    dur_labels  = ["1-Year", "2-Year", "3-Year"]

    matrix_html = (
        '<table style="width:100%;border-collapse:collapse;margin-top:8px;">'
        '<thead><tr style="border-bottom:2px solid #1f2937;">'
        '<th style="padding:10px 14px;text-align:left;color:#6b7280;font-size:0.75rem;'
        'text-transform:uppercase;letter-spacing:.07em;width:18%;">Player Tier</th>'
    )
    for dl in dur_labels:
        matrix_html += (
            f'<th style="padding:10px 14px;text-align:center;color:#6b7280;'
            f'font-size:0.75rem;text-transform:uppercase;letter-spacing:.07em;">{dl}</th>'
        )
    matrix_html += "</tr></thead><tbody>"

    for i, tier in enumerate(tiers_order):
        row_bg = "#0d1625" if i % 2 == 0 else "transparent"
        matrix_html += f'<tr style="background:{row_bg};border-bottom:1px solid #1a2535;">'
        matrix_html += (
            f'<td style="padding:12px 14px;color:#e2e8f0;font-weight:600;font-size:0.88rem;">'
            f'{tier}</td>'
        )
        for dur in [1, 2, 3]:
            row = next((r for r in _MATRIX if r[0] == tier and r[1] == dur), None)
            rec = row[2] if row else "Situational"
            rationale = row[3] if row else ""
            rc = REC_COLORS.get(rec, "#6b7280")
            matrix_html += (
                f'<td style="padding:12px 14px;text-align:center;vertical-align:top;">'
                f'<div style="display:inline-block;background:{rc}22;border:1px solid {rc};'
                f'border-radius:8px;padding:3px 14px;color:{rc};font-weight:700;'
                f'font-size:0.82rem;margin-bottom:6px;">{rec}</div>'
                f'<div style="color:#6b7280;font-size:0.78rem;line-height:1.5;'
                f'max-width:200px;margin:0 auto;">{rationale}</div>'
                f'</td>'
            )
        matrix_html += "</tr>"
    matrix_html += "</tbody></table>"
    card(matrix_html, extra_style="padding:0.8rem 1rem;overflow-x:auto;")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 4: Incentive Design Principles ────────────────────────────────
    st.markdown("#### Incentive Structure Design")
    st.markdown(
        '<p style="color:#6b7280;font-size:0.85rem;margin-top:-6px;">'
        'Three bonus structures worth understanding — each with a different strategic purpose.</p>',
        unsafe_allow_html=True,
    )

    inc1, inc2, inc3 = st.columns(3, gap="medium")

    inc1.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;padding:1.4rem;">'
        '<div style="color:#10b981;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Performance Triggers</div>'
        '<div style="color:#ffffff;font-size:0.95rem;font-weight:700;margin-bottom:8px;">'
        'Stat-Based Bonuses</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'Tie bonuses to individual statistical thresholds: PPG floors, '
        'rebounding averages, assist ratios, or minutes played minimums. '
        'These reward what you can directly measure, reduce moral hazard, '
        'and tie additional cost to the outcomes that actually move the needle.'
        '<br><br>'
        'Examples: <b style="color:#fff;">+$50K if avg 15+ PPG</b>, '
        '<b style="color:#fff;">+$25K if 30+ min/game in conference play</b>. '
        'Best for stars and solid starters where production is trackable and meaningful.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    inc2.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;padding:1.4rem;">'
        '<div style="color:#2774AE;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Team Outcome Bonuses</div>'
        '<div style="color:#ffffff;font-size:0.95rem;font-weight:700;margin-bottom:8px;">'
        'Win-Contingent Pay</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'Link bonuses to wins, conference titles, or tournament advancement milestones. '
        'A program that reaches the Sweet 16 has both proven the investment worked '
        'and generated additional revenue — making the bonus genuinely affordable '
        'at the moment it\'s owed.'
        '<br><br>'
        'Examples: <b style="color:#fff;">+$40K for NCAA Tournament appearance</b>, '
        '<b style="color:#fff;">+$75K for Sweet 16</b>. '
        'Works especially well for role players whose individual stats don\'t capture '
        'their actual contribution to the team.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    inc3.markdown(
        '<div style="background:#111827;border:1px solid #1f2937;border-radius:14px;padding:1.4rem;">'
        '<div style="color:#f59e0b;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:10px;">Availability Clauses</div>'
        '<div style="color:#ffffff;font-size:0.95rem;font-weight:700;margin-bottom:8px;">'
        'Games-Played Minimums</div>'
        '<div style="color:#9aa5b4;font-size:0.85rem;line-height:1.75;">'
        'Tie a portion of the deal to games played (e.g. full payment requires '
        'appearing in 80%+ of games). Protects against injury writeoffs on '
        'multi-year deals, and removes the perverse incentive for players '
        'to coast once their money is guaranteed.'
        '<br><br>'
        'Most relevant for <b style="color:#fff;">developmental and rotation players</b> '
        'on longer deals, where availability is as important as the production ceiling — '
        'you need them in the gym and on the floor, not on the medical table.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 5: Key Principles ─────────────────────────────────────────────
    st.markdown("#### Key Principles")

    card(
        '<div style="color:#6b7280;font-size:0.72rem;text-transform:uppercase;'
        'letter-spacing:.07em;margin-bottom:14px;">Strategic Takeaways</div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 28px;">'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #2774AE;">'
        '<b style="color:#fff;">Lock up developmental players early.</b> '
        'Pre-breakout multi-year deals are the highest-ROI move available to a '
        'mid-budget program. The cost of being wrong is small; the cost of not '
        'doing it is losing your investment to a rival.'
        '</div>'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #FFB300;">'
        '<b style="color:#fff;">Keep stars on short deals.</b> '
        'The departure risk at the top of the roster is real. '
        'One-year deals preserve the cap flexibility to reload — '
        'which matters more than trying to retain someone who may go pro regardless.'
        '</div>'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #10b981;">'
        '<b style="color:#fff;">Use incentives to bridge valuation gaps.</b> '
        'When you and the player disagree on their value, '
        'a lower guaranteed base plus meaningful upside bonuses lets both sides '
        'bet on the outcome they believe in — without either side overpaying upfront.'
        '</div>'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #ef4444;">'
        '<b style="color:#fff;">Never commit 3 years to a rotation player.</b> '
        'The ceiling is defined. Locking up a 15–20 min/game contributor through '
        'their entire eligibility forecloses upgrading that slot if something '
        'better comes through the portal.'
        '</div>'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #2774AE;">'
        '<b style="color:#fff;">Multi-year security wins bidding wars at lower AAV.</b> '
        'A player choosing between a $900K one-year offer and a '
        '$800K/yr two-year deal often takes the security. '
        'Guaranteed future earnings are worth real money to players — '
        'which means you can pay less annually while offering more total value.'
        '</div>'

        '<div style="color:#9aa5b4;font-size:0.88rem;line-height:1.7;padding-left:14px;'
        'border-left:2px solid #FFB300;">'
        '<b style="color:#fff;">Structure is leverage.</b> '
        'A program that thinks carefully about contract duration, '
        'escalator rates, and incentive triggers is playing a different game '
        'than one that just matches the highest offer. '
        'At $6.2M you can\'t outspend Kentucky — but you can out-structure them.'
        '</div>'

        '</div>',
        extra_style="padding:1.6rem;",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;color:#4b5563;font-size:0.75rem;'
    'padding:1rem 0;border-top:1px solid #1f2937;">'
    "UCLA MBB Rev-Share Model &nbsp;·&nbsp; Built with confirmed 2025-26 market data &nbsp;·&nbsp; "
    "Valuation MAE 10.7% on confirmed deals &nbsp;·&nbsp; "
    "All dollar figures are modeled estimates, not confirmed contracts"
    "</div>",
    unsafe_allow_html=True,
)
