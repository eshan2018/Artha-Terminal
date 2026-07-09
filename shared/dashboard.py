"""Nivesh Terminal — market dashboard orchestrator.

This is the central hub that:
1. Shows the sidebar risk profiler questionnaire
2. Loads all market data (prices, caps, metrics)
3. Applies risk-profile and type filters
4. Renders the dashboard header with live stats
5. Delegates each of the 7 tabs to its own module
6. Wraps every tab in try/except so one broken tab never crashes the page
"""
from __future__ import annotations  # Allow modern type hints

import html              # For escaping dynamic content in HTML (XSS prevention)
from datetime import datetime  # For timestamps

import pandas as pd      # For Series operations in source count
import streamlit as st   # Streamlit UI framework

# Import shared modules
from shared import IST   # Indian Standard Time timezone
from shared.calculations import RISK_ALLOWED, compute_metrics, get_risk_profile
from shared.data_loader import get_market_caps, get_risk_free_rate, get_usd_inr, load_market_data
from shared.tabs import (
    render_builder,   # Tab 1: Portfolio Builder
    render_charts,    # Tab 4: Price History
    render_glossary,  # Tab 6: Glossary
    render_heatmap,   # Tab 3: Performance Heatmap
    render_overview,  # Tab 0: Market Overview
    render_risk,      # Tab 5: Risk vs Return
    render_search,    # Tab 2: Search & Recommend
)
from shared.theme import inject_theme  # CSS design system


# ── Sidebar questionnaire ─────────────────────────────────────────────────────

def _questionnaire(label: str) -> tuple:
    """Render the risk profiler in the sidebar and return (profile, show_type, min_sharpe).

    Collects user inputs (age, horizon, drawdown comfort, knowledge, goal)
    and maps them to a SEBI 5-stage risk profile.
    """
    with st.sidebar:
        # Section header
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.12em;'
            f'text-transform:uppercase;color:var(--text-muted);margin-bottom:12px;">'
            f'Risk Profiler — {html.escape(label)}</div>',
            unsafe_allow_html=True,
        )
        # Questionnaire inputs
        age      = st.slider("Age", 18, 75, 32)             # Investor's age
        horizon  = st.slider("Investment horizon (yrs)", 1, 25, 7)  # How long they'll invest
        drawdown = st.select_slider("Drawdown comfort", ["Low", "Medium", "High"], value="Medium")
        knowledge = st.selectbox("Market knowledge", ["Beginner", "Intermediate", "Advanced"], index=1)
        goal     = st.selectbox("Primary goal",
                                ["Capital protection", "Balanced wealth", "Long-term growth"], index=1)

    # Calculate risk profile from questionnaire answers
    profile = get_risk_profile(age, horizon, drawdown, knowledge)

    # Goal overrides: capital protection pushes profile down, long-term growth pushes up
    if goal == "Capital protection":
        profile = "Conservative" if profile in {"Conservative", "Moderate"} else "Moderate"
    elif goal == "Long-term growth" and profile == "Balanced":
        profile = "Growth"

    with st.sidebar:
        # Show the computed profile
        st.success(f"Profile: **{profile}**")
        st.caption("SEBI 5-stage: Conservative → Moderate → Balanced → Growth → Aggressive")
        st.divider()

        # Navigation buttons
        if st.button("← Back to Home", use_container_width=True):
            st.switch_page("home.py")
        if st.button("⟳ Refresh Data", use_container_width=True):
            st.cache_data.clear()  # Clear all cached data
            st.rerun()             # Reload the page

        # Quick filters section
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.12em;'
            'text-transform:uppercase;color:var(--text-muted);margin:16px 0 10px;">Quick Filters</div>',
            unsafe_allow_html=True,
        )
        show_type  = st.radio("Asset type", ["All", "Equity", "ETF / Fund"], horizontal=False, index=0)
        min_sharpe = st.slider("Min Sharpe", -2.0, 3.0, -2.0, 0.1)

    return profile, show_type, min_sharpe


def _universe_arg(universe: list[dict]) -> tuple:
    """Convert universe list to a hashable tuple-of-tuples for Streamlit caching.

    Streamlit's @st.cache_data requires all arguments to be hashable.
    Dicts aren't hashable, so we convert each dict to a tuple of (key, value) pairs.
    """
    return tuple(tuple(a.items()) for a in universe)


# ── Main render entry point ───────────────────────────────────────────────────

def render_market_dashboard(
    market: str,           # "india" or "us"
    label: str,            # Display name: "India Market" or "US Market"
    universe: list[dict],  # List of 110 asset definitions from JSON
) -> None:
    """Main entry point for the market dashboard page.

    Called by pages/1_india_market.py and pages/2_us_market.py.
    Handles the full lifecycle: page config → data loading → filtering → tab rendering.
    """
    # Configure the page layout and title
    st.set_page_config(
        page_title=f"Nivesh Terminal — {label}",
        layout="wide",                       # Use full screen width
        initial_sidebar_state="expanded",    # Show sidebar for questionnaire
    )
    inject_theme()  # Inject the CSS design system

    # Run the sidebar questionnaire and get user preferences
    profile, show_type, min_sharpe = _questionnaire(label)

    # Fetch current USD/INR exchange rate (cached 5 min)
    usd_inr      = get_usd_inr()
    # Convert universe to hashable format for caching
    universe_raw = _universe_arg(universe)

    # Load price data for all 110 tickers (cached 15 min)
    _loading_placeholder = st.empty()
    _loading_placeholder.info("⏳ First load fetches 110 assets from yfinance — takes 20–30 seconds. Subsequent loads are instant (15 min cache).")
    with st.spinner(f"Downloading {label} price history from yfinance — please wait…"):
        df_daily, df_weekly = load_market_data(universe_raw, market, usd_inr)
    _loading_placeholder.empty()  # Clear the message once data is loaded
    if df_daily.empty:
        st.error("❌ No market data loaded. Check your internet connection or API keys, then refresh the page.")
        st.stop()  # Stop rendering — no data to show

    # Load market caps (cached 24 hours — separate wave after price data)
    with st.spinner("Loading market caps…"):
        df_daily.attrs["market_caps"] = get_market_caps(
            tuple(df_daily.columns), market, usd_inr
        )

    # Fetch live risk-free rate and compute all per-asset metrics
    rfr     = get_risk_free_rate()  # India 10Y G-Sec yield (cached 24h)
    metrics = compute_metrics(df_daily, df_weekly, universe_raw, rfr=rfr)

    # ── Apply filters based on user's risk profile ────────────────────────
    allowed  = RISK_ALLOWED[profile]  # Which asset categories this profile can see
    filtered = metrics[
        # Show assets in allowed categories, OR always show ETFs/funds
        metrics["Category"].isin(allowed) | metrics["Type"].isin(["etf", "fund"])
    ].copy()
    # Apply asset type filter (Equity only / ETF only / All)
    if show_type == "Equity":
        filtered = filtered[filtered["Type"] == "equity"]
    elif show_type == "ETF / Fund":
        filtered = filtered[filtered["Type"].isin(["etf", "fund"])]
    # Apply minimum Sharpe filter (keep NaN Sharpe so missing data isn't hidden)
    filtered = filtered[filtered["Sharpe"].isna() | (filtered["Sharpe"] >= min_sharpe)]

    # ── Dashboard header ──────────────────────────────────────────────────
    ts         = datetime.now(IST).strftime("%d %b %Y, %H:%M:%S IST")  # Current time
    # Count how many tickers came from each data source
    src_counts = pd.Series(df_daily.attrs.get("sources", {})).value_counts().to_dict()
    source_note = ", ".join(f"{k}: {v}" for k, v in src_counts.items()) or "N/A"
    fetched_at  = df_daily.attrs.get("fetched_at", "unknown")

    # Render the dashboard title with live stats
    flag = "🇮🇳" if market == "india" else "🇺🇸"
    st.markdown(
        f'<div class="dash-title">{flag} Nivesh Terminal — {html.escape(label)}</div>'
        f'<div class="dash-sub">'
        f'{ts} &nbsp;|&nbsp; USD/INR ₹{usd_inr:.2f} &nbsp;|&nbsp; {html.escape(source_note)}'
        f' &nbsp;|&nbsp; <span style="color:var(--text-muted)">data fetched {html.escape(fetched_at)}'
        f' · refreshes every 15 min</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # SEBI compliance disclaimer banner
    st.markdown(
        '<div style="background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.18);'
        'border-radius:6px;padding:8px 14px;font-size:0.7rem;line-height:1.5;'
        'color:var(--text-muted);margin-top:8px;">'
        '⚠️ <strong>Educational tool only.</strong> Nothing on this dashboard constitutes '
        'investment advice. Past performance does not guarantee future results. '
        'Consult a SEBI-registered investment adviser before making financial decisions.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Create the 7 dashboard tabs ───────────────────────────────────────
    tabs = st.tabs([
        "📊 Market Overview",
        "🎯 Portfolio Builder",
        "🔍 Search & Recommend",
        "🔥 Performance Heatmap",
        "📈 Price History",
        "⚖️ Risk vs Return",
        "📖 Glossary",
    ])

    # Shared context dict — passed to every tab's render function
    ctx = dict(
        filtered=filtered,    # Metrics filtered by risk profile
        metrics=metrics,      # Full unfiltered metrics (all 110 assets)
        df_daily=df_daily,    # Daily close prices (2 years)
        df_weekly=df_weekly,  # Weekly close prices (20 years)
        market=market,        # "india" or "us"
        usd_inr=usd_inr,     # Current exchange rate
        profile=profile,      # User's risk profile string
        rfr=rfr,              # Live risk-free rate (decimal)
    )

    # Map tab names to their render functions
    _TAB_RENDERS = [
        ("Market Overview",  render_overview),
        ("Portfolio Builder", render_builder),
        ("Search",           render_search),
        ("Heatmap",          render_heatmap),
        ("Price History",    render_charts),
        ("Risk vs Return",   render_risk),
        ("Glossary",         render_glossary),
    ]

    # Render each tab with error isolation — one broken tab won't crash the rest
    for tab_ctx, (tab_name, tab_fn) in zip(tabs, _TAB_RENDERS):
        with tab_ctx:
            try:
                tab_fn(**ctx)  # Call the tab's render function with all shared context
            except Exception as _err:
                # Show a friendly error message + expandable stack trace
                st.error(f"**{tab_name}** tab encountered an error and could not render.")
                with st.expander("Technical details (click to expand)"):
                    st.exception(_err)
