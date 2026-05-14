"""Tab 3 — Performance Heatmap: treemap, sunburst, calendar heatmap + top movers."""
from __future__ import annotations  # Allow modern type hints

import numpy as np               # For conditional grouping (np.where)
import pandas as pd              # DataFrame operations for calendar pivot
import plotly.express as px      # High-level Plotly charts (treemap, sunburst, imshow)
import streamlit as st           # Streamlit UI framework

# Import shared display helpers and theme constants
from shared.tabs._helpers import _MARGIN, asset_options, fmt_pct, ticker_from
from shared.theme import PLOTLY_THEME


def render(*, filtered, metrics, df_daily, df_weekly, market, usd_inr, profile, rfr, **_):
    """Render the Performance Heatmap tab: treemap / sector sunburst / calendar
    heatmap + top 5 gainers and decliners."""

    # ── User controls: period and view type ───────────────────────────────────
    c_period, c_view = st.columns([1, 2])             # Two columns for the radio buttons
    period_choice = c_period.radio("Return period", ["1M%", "1Y%"], horizontal=True)  # Which return to color by
    view_choice   = c_view.radio("View", ["Treemap", "Sector Sunburst", "Calendar Heatmap"], horizontal=True)

    # Prepare the data — group ETFs/funds together, keep equity by sector
    heat = filtered.copy()
    heat["Group"] = np.where(                         # Create a grouping column
        heat["Type"].isin(["etf", "fund"]),            # If asset is ETF or fund…
        "ETF / Fund",                                  # …put it in a single group
        heat["Sector"]                                 # …otherwise use its sector name
    )

    # ── VIEW 1: Treemap ──────────────────────────────────────────────────────
    if view_choice == "Treemap":
        heat_clean = heat.dropna(subset=[period_choice]).copy()  # Remove rows with no return data
        fig_h = px.treemap(
            heat_clean,
            path=["Group", "Name"],                     # Hierarchy: Group → Asset Name
            values=heat_clean[period_choice].abs(),     # Box size = magnitude of return (abs so negatives have area)
            color=period_choice,                        # Color = actual return value (green/red)
            color_continuous_scale="RdYlGn",            # Red-Yellow-Green diverging scale
            color_continuous_midpoint=0,                # Zero return = yellow (midpoint)
            custom_data=[period_choice, "Ticker", "Sharpe"],  # Extra data for hover tooltip
        )
        # Customise what text shows inside each treemap box
        fig_h.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata[0]:.1f}%",  # Name + return %
            textfont_size=12,
            hovertemplate="<b>%{label}</b><br>Return: %{customdata[0]:.2f}%<br>"
                          "Ticker: %{customdata[1]}<br>Sharpe: %{customdata[2]:.2f}<extra></extra>",
        )
        fig_h.update_layout(**PLOTLY_THEME, height=620, margin=_MARGIN)  # Apply dark theme
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

    # ── VIEW 2: Sector Sunburst ──────────────────────────────────────────────
    elif view_choice == "Sector Sunburst":
        sb_clean = heat.dropna(subset=[period_choice]).copy()           # Remove NaN returns
        sb_clean["AbsRet"] = sb_clean[period_choice].abs().clip(lower=0.01)  # Sector slice size (min 0.01 so zero-return assets still show)
        fig_sb = px.sunburst(
            sb_clean,
            path=["Group", "Name"],                   # Hierarchy: Group → Asset Name
            values="AbsRet",                          # Slice size = magnitude of return
            color=period_choice,                      # Color = actual return value
            color_continuous_scale="RdYlGn",          # Red-Yellow-Green diverging scale
            color_continuous_midpoint=0,               # Zero = yellow
        )
        fig_sb.update_layout(**PLOTLY_THEME, height=620, margin=_MARGIN)
        st.plotly_chart(fig_sb, use_container_width=True, config={"displayModeBar": False})

    # ── VIEW 3: Calendar Heatmap (GitHub-style daily returns grid) ───────────
    elif view_choice == "Calendar Heatmap":
        # Let user pick which asset to show the calendar for (top 20 by default)
        cal_opts = asset_options(filtered.head(20))
        cal_sel  = st.selectbox("Select asset for calendar heatmap", cal_opts, label_visibility="collapsed")
        cal_tick = ticker_from(cal_sel)                # Extract the ticker symbol from the selection string

        if cal_tick in df_daily.columns:
            cal_prices = df_daily[cal_tick].dropna()    # Get the daily close prices for this asset
            daily_rets = cal_prices.pct_change().dropna() * 100  # Calculate daily % returns
            daily_rets.index = pd.to_datetime(daily_rets.index)  # Ensure index is datetime

            # Build a DataFrame with date parts for the pivot table
            cal_df = daily_rets.reset_index()
            cal_df.columns = ["Date", "Return"]
            cal_df["Week"]    = cal_df["Date"].dt.isocalendar().week.astype(int)  # ISO week number (1-52)
            cal_df["Weekday"] = cal_df["Date"].dt.weekday       # 0=Mon, 1=Tue, ..., 6=Sun
            cal_df["Year"]    = cal_df["Date"].dt.year           # Calendar year

            # Keep only the last 2 years of data
            recent = cal_df[cal_df["Year"] >= cal_df["Year"].max() - 1]

            # Pivot into a grid: rows=weekday, columns=week number, values=avg daily return
            pivot  = recent.pivot_table(index="Weekday", columns="Week", values="Return", aggfunc="mean")

            # Render as a heatmap image
            fig_cal = px.imshow(
                pivot,
                color_continuous_scale="RdYlGn",      # Green=positive, Red=negative
                color_continuous_midpoint=0,            # Zero=neutral
                labels=dict(color="Daily Return %"),
                y=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][:len(pivot)],  # Y-axis labels
                aspect="auto",                          # Stretch to fill
            )
            fig_cal.update_layout(
                **PLOTLY_THEME, height=260, margin=_MARGIN,
                title=dict(text=f"{cal_tick} — Daily Return Calendar (last 2 years)", font=dict(size=12)),
            )
            st.plotly_chart(fig_cal, use_container_width=True, config={"displayModeBar": False})
            st.caption("Each cell = average daily return for that weekday in that week. Green = positive, Red = negative.")

    # ── Top movers panel ─────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)  # Small spacer

    m1, m2 = st.columns(2)  # Two columns: gainers on left, decliners on right

    # Get the 5 best and 5 worst performers for the selected period
    top5 = filtered.dropna(subset=[period_choice]).nlargest(5, period_choice)   # Top 5 gainers
    bot5 = filtered.dropna(subset=[period_choice]).nsmallest(5, period_choice)  # Top 5 decliners

    # Render the top gainers list
    with m1:
        st.markdown(f'<div class="intel-section-title">Top 5 Gainers ({period_choice})</div>', unsafe_allow_html=True)
        for _, row in top5.iterrows():
            st.markdown(
                f'<div class="intel-row">'
                f'<span class="intel-row-label">{row["Name"][:24]}</span>'   # Truncate long names
                f'<span class="intel-row-value t-green">{fmt_pct(row[period_choice])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Render the top decliners list
    with m2:
        st.markdown(f'<div class="intel-section-title">Top 5 Decliners ({period_choice})</div>', unsafe_allow_html=True)
        for _, row in bot5.iterrows():
            st.markdown(
                f'<div class="intel-row">'
                f'<span class="intel-row-label">{row["Name"][:24]}</span>'
                f'<span class="intel-row-value t-red">{fmt_pct(row[period_choice])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
