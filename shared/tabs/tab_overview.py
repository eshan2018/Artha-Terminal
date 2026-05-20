"""Tab 0 — Market Overview: pulse bar + sortable data table."""
from __future__ import annotations  # Allow modern type hints

import pandas as pd     # DataFrame operations
import streamlit as st  # Streamlit UI framework

# Import formatting helpers from shared modules
from shared.calculations import fmt_inr, ret_color       # INR formatter + cell coloring
from shared.tabs._helpers import _MARGIN, fmt_pct, chg_color, sharpe_stars  # Display helpers


def render(*, filtered, metrics, df_daily, df_weekly, market, usd_inr, profile, rfr, **_):
    """Render the Market Overview tab: pulse bar (adv/dec/breadth) + sortable asset table.

    ``filtered`` is the metrics DataFrame already narrowed to the user's risk profile.
    """
    # ── Market Pulse Bar ──────────────────────────────────────────────────────
    # Count how many assets went up (advancing) vs down (declining) today
    adv   = int((filtered["1D%"].dropna() > 0).sum())   # Number of assets with positive 1-day return
    dec   = int((filtered["1D%"].dropna() < 0).sum())   # Number of assets with negative 1-day return
    tot   = adv + dec                                    # Total assets with a 1-day return value
    brd   = f"{round(adv/tot*100) if tot else 0}% Up"   # Breadth: what % of assets are up today
    avg_s = filtered["Sharpe"].dropna().mean()           # Average Sharpe ratio across all filtered assets
    avg_r = filtered["1Y%"].dropna().mean()              # Average 1-year return across all filtered assets
    n_pos = int((filtered["1Y%"].dropna() > 0).sum())   # How many assets have positive 1Y return

    # Render the pulse bar as a horizontal strip of 5 KPI cells
    st.markdown(f"""
    <div class="pulse-bar">
      <div class="pulse-item">
        <div class="pulse-label">Market Breadth</div>
        <div class="pulse-value t-accent">{brd}</div>
        <div class="pulse-delta t-muted">{adv} adv · {dec} dec</div>
      </div>
      <div class="pulse-item">
        <div class="pulse-label">Avg Sharpe</div>
        <div class="pulse-value" style="color:{'var(--green)' if avg_s>0.5 else 'var(--red)'}">{avg_s:.2f}</div>
        <div class="pulse-delta t-muted">risk-adjusted</div>
      </div>
      <div class="pulse-item">
        <div class="pulse-label">Avg 1Y Return</div>
        <div class="pulse-value" style="color:{chg_color(avg_r)}">{fmt_pct(avg_r)}</div>
        <div class="pulse-delta t-muted">filtered universe</div>
      </div>
      <div class="pulse-item">
        <div class="pulse-label">Positive 1Y</div>
        <div class="pulse-value t-green">{n_pos}</div>
        <div class="pulse-delta t-muted">of {len(filtered)} assets</div>
      </div>
      <div class="pulse-item">
        <div class="pulse-label">In Universe</div>
        <div class="pulse-value">{len(filtered)}</div>
        <div class="pulse-delta t-muted">Profile: {profile}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sortable overview table ───────────────────────────────────────────────
    # Select only the columns we want to display in the table
    overview = filtered[[
        "Ticker", "Name", "Sector", "Type",
        "1D%", "1W%", "1M%", "1Y%", "3Y%",
        "Sharpe", "Volatility", "Vol 1M", "Market Cap",
    ]].copy()

    # Add a human-readable Sharpe column with star ratings (★★★ / ★★ / ★ / ✕)
    overview["Sharpe ★  (score)"] = overview["Sharpe"].apply(sharpe_stars)

    # Format market cap as ₹ string (e.g. "₹1.2L Cr") or dash if missing
    overview["Market Cap"] = overview["Market Cap"].apply(
        lambda x: fmt_inr(x) if x is not None and pd.notna(x) else "—"
    )

    # Drop the raw numeric Sharpe column (replaced by star-rated version)
    overview = overview.drop(columns=["Sharpe"])

    # Reset index to start from 1 (nicer display in the table)
    overview.index = range(1, len(overview) + 1)

    # Show a legend explaining the star ratings and volatility types
    st.caption(
        "★★★ ≥ 1.5  ·  ★★ 0.5–1.49  ·  ★ 0–0.49  ·  ✕ negative Sharpe  ·  "
        "Volatility = weekly×√52 (long-term)  ·  Vol 1M = daily×√252 (short-term)"
    )

    # Render the interactive Streamlit dataframe with conditional coloring
    st.dataframe(
        overview.style
            # Color return columns red/green based on sign
            .map(ret_color, subset=["1D%", "1W%", "1M%", "1Y%", "3Y%"])
            # Format return columns with sign and 2 decimal places
            .format(
                {"1D%": "{:+.2f}%", "1W%": "{:+.2f}%", "1M%": "{:+.2f}%",
                 "1Y%": "{:+.2f}%", "3Y%": "{:+.2f}%",
                 "Volatility": "{:.2f}%", "Vol 1M": "{:.2f}%"},
                na_rep="—",  # Show dash for missing values
            )
            # Apply dark background matching the terminal theme
            .set_properties(**{"background-color": "#0d1526", "color": "#f0f6ff"}),
        use_container_width=True,  # Stretch table to full page width
        height=600,                # Fixed height with scroll for 110 rows
    )
