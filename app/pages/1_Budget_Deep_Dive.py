"""
Page 2: Budget Deep Dive — conference peer comparison.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd
from src.budget.allocator import allocate_budget

st.set_page_config(page_title="Budget Deep Dive", page_icon="📊", layout="wide")
st.title("Budget Deep Dive — Conference Peer Comparison")
st.markdown(
    "How does UCLA's MBB allocation compare to peers? "
    "All figures use the same $21.3M House settlement cap — only the sport-share "
    "splits and collective/NIL estimates differ."
)

PEERS = {
    "UCLA — House formula (base case)":  {"fb":75,"mbb":15,"nil":3_000_000,"note":"Jarmond confirmed 75/15/5/5 formula (LA Times, June 2025)"},
    "UCLA — 25% MBB allocation":         {"fb":65,"mbb":25,"nil":3_000_000,"note":"If UCLA prioritised basketball like Kentucky"},
    "Kentucky (reported ~$22M total)":   {"fb":65,"mbb":30,"nil":16_800_000,"note":"$5.3M rev-share + $16.7M collective"},
    "Duke (reported ~$12M total)":       {"fb":68,"mbb":22,"nil":7_600_000,"note":"$4.7M rev-share + ~$7.6M NIL"},
    "Average Power Four":                {"fb":75,"mbb":14,"nil":2_800_000,"note":"Opendorse avg: $4.2M rev-share + $3M NIL"},
}

rows = []
CAP = 21_320_000
for label, cfg in PEERS.items():
    wbb  = 5
    other = 100 - cfg["fb"] - cfg["mbb"] - wbb
    alloc = allocate_budget(
        year=label,
        rev_share_cap=CAP,
        sport_shares={
            "Football":           cfg["fb"] / 100,
            "Men's Basketball":   cfg["mbb"] / 100,
            "Women's Basketball": wbb / 100,
            "Olympic / Other":    other / 100,
        },
        mbb_nil_low=max(0, cfg["nil"] - 1_000_000),
        mbb_nil_base=cfg["nil"],
        mbb_nil_high=cfg["nil"] + 1_500_000,
    )
    rows.append({
        "Program / Scenario": label,
        "MBB %": f"{cfg['mbb']}%",
        "Rev-Share (MBB)": f"${alloc.mbb_rev_share:,}",
        "NIL / Collective": f"${cfg['nil']:,}",
        "Total Budget": f"${alloc.mbb_total_base:,}",
        "vs UCLA base": f"{(alloc.mbb_total_base / (CAP*0.15 + 3_000_000) - 1)*100:+.0f}%",
        "Note": cfg["note"],
    })

df = pd.DataFrame(rows).set_index("Program / Scenario")
st.dataframe(df, use_container_width=True)

st.markdown("""
**Reading this table:**
- A single percentage-point shift in UCLA's MBB allocation (15% → 16%) adds ~$213K rev-share.
- Shifting to 25% MBB adds ~$2.1M in rev-share alone — enough to move from Balanced Veteran to Stars-and-Scrubs territory.
- The gap between UCLA and Kentucky is overwhelmingly the collective/NIL layer, not the rev-share formula.
- UCLA's debt burden (~$167.7M) constrains how aggressively they can supplement with collective money.
""")
