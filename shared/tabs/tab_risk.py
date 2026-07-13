"""Tab 5 — Risk vs Return: scatter plot, Security Market Line, quadrants + drawdown panel."""
from __future__ import annotations  # Allow modern type hints

import numpy as np               # For generating SML line coordinates
import plotly.express as px       # For the scatter plot
import plotly.graph_objects as go  # For adding SML line and annotations
import streamlit as st            # Streamlit UI framework

# Import financial functions and display helpers
from shared.calculations import RISK_FREE_RATE, get_max_drawdown, get_rolling_drawdown
from shared.tabs._helpers import _MARGIN, _PGRID, asset_options, fmt_num, ticker_from
from shared.theme import GRID_COLOR, PLOTLY_THEME


def render(*, filtered, metrics, df_daily, df_weekly, market, usd_inr, profile, rfr, **_):
    """Render the Risk vs Return tab: scatter plot with dynamic Security Market Line,
    quadrant labels, What-If ticker highlight, and drawdown analysis panel."""

    # Filter to assets that have all 3 required fields (some may have NaN)
    scatter = filtered.dropna(subset=["Volatility", "1Y%", "Sharpe"]).copy()
    if scatter.empty:
        st.info("Not enough data for the risk-return plot.")
        return

    # Bubble size based on Sharpe ratio magnitude (bigger bubble = more notable Sharpe)
    scatter["Bubble"] = scatter["Sharpe"].abs().clip(lower=0.1) * 20

    # Create the scatter plot: X = Volatility (risk), Y = 1Y Return (reward)
    fig_rv = px.scatter(scatter, x="Volatility", y="1Y%",
                        size="Bubble", color="Sector", symbol="Type",
                        hover_name="Name",
                        hover_data={"Ticker": True, "Sharpe": ":.2f", "Bubble": False},
                        size_max=40,
                        labels={"Volatility": "Annualised Volatility (%)", "1Y%": "1Y Return (%)"})

    # ── Security Market Line (SML) ────────────────────────────────────────
    # The SML shows the theoretical return for each level of risk
    # slope = market Sharpe ratio = (median_return - risk_free_rate) / median_volatility
    x_range = np.linspace(float(scatter["Volatility"].min()) * 0.8,
                          float(scatter["Volatility"].max()) * 1.1, 60)
    _med_ret = float(scatter["1Y%"].median())       # Median return across all assets
    _med_vol = float(scatter["Volatility"].median()) # Median volatility
    # Dynamic slope computed from actual market data (not hardcoded)
    sml_slope = (_med_ret - rfr * 100) / _med_vol if _med_vol > 0 else 0.5
    sml_y = rfr * 100 + sml_slope * x_range  # SML line: y = rfr + slope × x
    fig_rv.add_trace(go.Scatter(x=x_range, y=sml_y, name="Security Market Line",
                                line=dict(color="rgba(255,179,0,0.35)", width=1.5, dash="dash"),
                                hoverinfo="skip"))

    # ── Median crosshairs (divide the plot into 4 quadrants) ──────────────
    med_vol = float(scatter["Volatility"].median())
    med_ret = float(scatter["1Y%"].median())
    fig_rv.add_vline(x=med_vol, line_color="rgba(148,163,184,0.2)", line_dash="dot")
    fig_rv.add_hline(y=med_ret, line_color="rgba(148,163,184,0.2)", line_dash="dot")

    # ── Quadrant labels (help users understand each zone) ─────────────────
    for text, x_val, y_val, color in [
        ("HIGH RETURN · LOW RISK",  scatter["Volatility"].min()*1.05, scatter["1Y%"].max()*0.9,  "rgba(0,230,118,0.4)"),   # Best zone (green)
        ("HIGH RETURN · HIGH RISK", scatter["Volatility"].max()*0.7,  scatter["1Y%"].max()*0.9,  "rgba(255,215,0,0.4)"),   # Good but risky (gold)
        ("LOW RETURN · LOW RISK",   scatter["Volatility"].min()*1.05, scatter["1Y%"].min()*0.9,  "rgba(148,163,184,0.4)"), # Boring (grey)
        ("AVOID ZONE",              scatter["Volatility"].max()*0.7,  scatter["1Y%"].min()*0.9,  "rgba(244,67,54,0.4)"),   # Worst zone (red)
    ]:
        fig_rv.add_annotation(x=x_val, y=y_val, text=text, showarrow=False,
                               font=dict(size=9, color=color), xanchor="left")

    # ── Highlight the "What-If" ticker from Portfolio Builder tab ─────────
    # If user selected a ticker in tab_builder, show it as a gold star here
    _wi_ticker = st.session_state.get("_wi_ticker_rv")
    _wi_ret    = st.session_state.get("_wi_ret_rv")
    _wi_vol    = st.session_state.get("_wi_vol_rv")
    if _wi_ticker and _wi_ret is not None and _wi_vol is not None:
        fig_rv.add_trace(go.Scatter(x=[_wi_vol], y=[_wi_ret],
                                    mode="markers+text", name=f"Your pick: {_wi_ticker}",
                                    marker=dict(color="#ffd700", size=18, symbol="star",
                                                line=dict(color="#ffd700", width=1)),
                                    text=[_wi_ticker], textposition="top center",
                                    textfont=dict(size=10, color="#ffd700")))

    # Apply theme and render the chart
    fig_rv.update_layout(**PLOTLY_THEME, height=560, margin=_MARGIN)
    fig_rv.update_xaxes(**_PGRID)
    fig_rv.update_yaxes(**_PGRID)
    st.plotly_chart(fig_rv, use_container_width=True, config={"displayModeBar": False})

    # ── Drawdown analysis panel ───────────────────────────────────────────
    st.markdown('<div class="intel-section-title" style="margin-top:4px;">Drawdown Analysis — select an asset</div>',
                unsafe_allow_html=True)
    dd_opts   = asset_options(filtered)                    # Build dropdown options
    dd_sel    = st.selectbox("Asset for drawdown", dd_opts, label_visibility="collapsed")
    dd_ticker = ticker_from(dd_sel)                        # Extract ticker from selection

    if dd_ticker in df_weekly.columns:
        dd_prices = df_weekly[dd_ticker].dropna()          # Get weekly prices for this asset
        dd_series = get_rolling_drawdown(dd_prices)        # Calculate drawdown at every date

        # Plot the underwater chart (red area below zero line)
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=dd_series.index, y=dd_series.values,
                                    fill="tozeroy", fillcolor="rgba(244,67,54,0.12)",
                                    line=dict(color="#f44336", width=1.4), name="Drawdown"))
        fig_dd.add_hline(y=0, line_color="rgba(148,163,184,0.3)")  # Zero line
        fig_dd.update_layout(**PLOTLY_THEME, height=200, margin=_MARGIN, yaxis_title="Drawdown %")
        fig_dd.update_xaxes(showgrid=False)
        fig_dd.update_yaxes(**_PGRID)
        st.plotly_chart(fig_dd, use_container_width=True, config={"displayModeBar": False})

        # Show the maximum drawdown figure
        st.caption(f"Max drawdown: **{fmt_num(get_max_drawdown(dd_prices))}%** — deepest peak-to-trough over 20Y weekly data.")
