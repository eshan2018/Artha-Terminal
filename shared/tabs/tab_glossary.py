"""Tab 6 — Glossary: searchable term cards + live Sharpe playground."""
from __future__ import annotations  # Allow modern type hints

import pandas as pd    # For the quick-reference DataFrame
import streamlit as st  # Streamlit UI framework

from shared.theme import PLOTLY_THEME  # Dark theme for Plotly charts (unused here but kept for consistency)


# ── Glossary term definitions ─────────────────────────────────────────────────
# Each tuple: (short_name, search_keywords, display_title, markdown_body, accent_color)
# search_keywords are used for fuzzy matching when the user types in the search box
_TERMS = [
    ("Sharpe Ratio", "sharpe ratio risk",
     "Sharpe Ratio",
     "**Formula:** `(Annualised Mean Weekly Return − Risk-Free Rate) / Annualised Volatility`\n\n"
     "Measures how much excess return you earn per unit of risk. "
     "Nivesh Terminal uses the **annualised mean of weekly returns** (mean weekly return × 52) as the numerator "
     "— more statistically robust than a point-in-time 1Y return. "
     "The risk-free rate is fetched live from India's 10Y G-Sec yield (^INBMK via NSE), with a 6.5% fallback.\n\n"
     "**Example:** A Sharpe of 1.2 means for every 1% of risk taken, you earned 1.2% above the risk-free rate.",
     "var(--accent)"),

    ("CAGR", "cagr compound annual growth rate return",
     "CAGR — Compound Annual Growth Rate",
     "The constant annual growth rate that connects a start value to an end value over N years.\n\n"
     "`CAGR = (End / Start)^(1/N) − 1`\n\n"
     "All 1Y/3Y/5Y/10Y returns on this platform use `pd.DateOffset` calendar matching — "
     "never hardcoded offsets.",
     "var(--green)"),

    ("SIP Future Value", "sip systematic investment plan compounding",
     "SIP Future Value",
     "The compounded value of equal annual contributions invested at a constant CAGR:\n\n"
     "`FV = P × (((1+r)^n − 1) / r) × (1+r)`\n\n"
     "Most platforms incorrectly use the lump-sum formula for SIP projections. "
     "The difference is **3–5× over 20 years**. Year-0 SIP always returns ₹0 (no investment yet).",
     "var(--gold)"),

    ("Volatility", "volatility standard deviation risk",
     "Annualised Volatility",
     "Standard deviation of periodic returns, scaled to annual. "
     "Nivesh Terminal shows two versions:\n\n"
     "- **Long-term Vol** = `σ(weekly returns) × √52` — suitable for 1Y+ holding periods\n"
     "- **Vol 1M** = `σ(daily returns) × √252` — suitable for ~1M holding period\n\n"
     "Higher volatility = wider return distribution = higher risk.",
     "var(--purple)"),

    ("Max Drawdown", "drawdown loss peak trough",
     "Maximum Drawdown",
     "The largest peak-to-trough decline in portfolio value over a period:\n\n"
     "`MDD = (Trough − Peak) / Peak × 100`\n\n"
     "A drawdown of −35% means the asset fell 35% from its peak before recovering. "
     "Critical for understanding tail risk.",
     "var(--red)"),

    ("RSI", "rsi relative strength index overbought oversold momentum",
     "RSI — Relative Strength Index",
     "A momentum oscillator ranging 0–100:\n\n"
     "- **RSI > 70**: Overbought — possible pullback\n"
     "- **RSI < 30**: Oversold — possible bounce\n"
     "- **RSI 40–60**: Neutral zone\n\n"
     "Nivesh Terminal uses the 14-day EMA-smoothed RSI.",
     "var(--accent)"),

    ("SEBI Risk Categories", "sebi risk profile conservative aggressive",
     "SEBI-Aligned 5-Stage Risk Scale",
     "| Profile | Sharpe Floor | Asset Categories |\n"
     "|---------|-------------|------------------|\n"
     "| Conservative | Any | Safe Haven only |\n"
     "| Moderate | 0.3+ | Safe Haven + Stabilizer |\n"
     "| Balanced | 0.5+ | All categories |\n"
     "| Growth | 0.7+ | Stabilizer + High Growth |\n"
     "| Aggressive | Any | All categories, full conviction |\n\n"
     "Based on SEBI Investor Adviser Regulations 2013 and AMFI demographic data.",
     "var(--green)"),

    ("Efficient Frontier", "efficient frontier portfolio theory mpt markowitz",
     "Efficient Frontier (Modern Portfolio Theory)",
     "The set of portfolios that maximise return for a given level of risk.\n\n"
     "Nivesh Terminal plots **2,000 random weight combinations** (Monte Carlo) to approximate the frontier. "
     "The gold star = max Sharpe portfolio. The cyan diamond = min volatility portfolio.\n\n"
     "Portfolios **above and to the left** of the frontier are impossible. "
     "Portfolios **below** are inefficient — you can do better.",
     "var(--gold)"),
]


def render(*, filtered, metrics, df_daily, df_weekly, market, usd_inr, profile, rfr, **_):
    """Render the Glossary tab: searchable financial term cards and a live
    Sharpe ratio playground with interactive sliders."""

    # ── Search box to filter glossary terms ───────────────────────────────────
    search_term = st.text_input(
        "Search glossary…",
        placeholder="e.g. Sharpe, CAGR, SIP, drawdown",
        label_visibility="collapsed",
    )

    # Filter terms: show all if no search, or only matching ones
    visible = [t for t in _TERMS if not search_term or search_term.lower() in t[1].lower()]

    # Show a message if no terms match the search query
    if not visible:
        st.info("No terms match your search.")

    # Render each matching term as an expandable card
    for (short, _, title, body, __) in visible:
        # Auto-expand the term if the search matches its title
        with st.expander(f"**{short}**", expanded=(search_term.lower() in title.lower() if search_term else False)):
            st.markdown(body)  # Render the term's full explanation in Markdown

    # ── Live Sharpe Playground ────────────────────────────────────────────────
    st.divider()  # Visual separator
    st.markdown("### Live Sharpe Playground")
    st.caption("Adjust the sliders to see how Sharpe responds in real time.")

    # Three sliders: return, volatility, and risk-free rate
    pg1, pg2, pg3 = st.columns(3)
    pg_ret  = pg1.slider("Annual Return %",   -20.0, 50.0, 12.0, 0.5)   # Expected annual return
    pg_vol  = pg2.slider("Volatility %",        1.0, 60.0, 18.0, 0.5)   # Annual volatility
    pg_rfr  = pg3.slider("Risk-Free Rate %",    0.0, 15.0,               # Risk-free rate
                          round((rfr or 0.065) * 100, 1), 0.1)           # Default from live rfr

    # Calculate Sharpe: (Return - RFR) / Volatility
    pg_sharpe = (pg_ret - pg_rfr) / pg_vol if pg_vol > 0 else 0

    # Choose display color and label based on Sharpe value
    pg_color = "var(--green)" if pg_sharpe > 0.5 else ("var(--gold)" if pg_sharpe > 0 else "var(--red)")
    pg_label = ("Good" if pg_sharpe > 1
                else ("Acceptable" if pg_sharpe > 0.5
                      else ("Marginal" if pg_sharpe > 0 else "Destroys Value")))

    # Render the computed Sharpe as a big styled number
    st.markdown(
        f'<div class="metric-band" style="text-align:center;border-left-color:{pg_color};">'
        f'<div class="m-label">Sharpe Ratio</div>'
        f'<div class="m-value" style="color:{pg_color};font-size:2rem;">{pg_sharpe:.3f}</div>'
        f'<div style="color:{pg_color};font-size:0.8rem;margin-top:4px;">{pg_label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Quick Reference Table ─────────────────────────────────────────────────
    st.markdown("**Quick Reference**")
    ref_data = {
        "Sharpe":        ["> 2.0", "1.0 – 2.0", "0.5 – 1.0", "0 – 0.5", "< 0"],
        "Interpretation":["Exceptional", "Good", "Acceptable", "Poor", "Destroys Value"],
        "Typical Assets":["Top ETFs in bull market", "Quality large-caps",
                          "Diversified portfolio", "High-vol speculative", "Consistent value destroyer"],
    }
    # Display the reference table without row indices
    st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)
