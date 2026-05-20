"""AI-powered 3-statement financial analysis via Groq (free tier).

Uses Llama 3.3 70B to analyse the connections between a company's
Income Statement, Balance Sheet, and Cash Flow Statement.
"""
from __future__ import annotations  # Allow modern type hints

import os              # For reading environment variables (API keys)
import math            # For isnan/isinf checks
import streamlit as st # For caching and secrets management
import pandas as pd    # For DataFrame handling of financial data
import yfinance as yf  # For fetching financial statements
from groq import Groq  # For calling Llama 3.3 AI model


def _fmt_m(val, label: str) -> str:
    """Format a financial value in millions (e.g. '$1,234.5M').
    Returns 'not available' if the value is missing, NaN, or infinity."""
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return f"{label}: not available"
    return f"{label}: ${float(val) / 1e6:,.1f}M"  # Convert raw number to millions


def _get(df: pd.DataFrame, *keys) -> tuple[float | None, float | None]:
    """Extract current-year and prior-year values from a financial statement.

    yfinance returns financial data with varying column names across companies,
    so we try multiple possible names (keys) and return the first match.
    Returns (current_year_value, prior_year_value) as a tuple.
    """
    for k in keys:
        if k in df.index:
            row = df.loc[k]
            # Column 0 = most recent year, Column 1 = prior year
            cur   = float(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else None
            prior = float(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else None
            return cur, prior
    return None, None  # No matching row found in any of the possible names


def _extract(ticker: str) -> dict | None:
    """Pull key financial figures from yfinance for the AI prompt.

    Returns a dictionary with 11 fields (Net Income, OCF, ICF, D&A, etc.)
    or None if the data is unavailable.
    """
    try:
        t   = yf.Ticker(ticker)
        inc = t.financials      # Income Statement
        bal = t.balance_sheet   # Balance Sheet
        cf  = t.cashflow        # Cash Flow Statement

        # If any of the 3 statements is empty, we can't do the analysis
        if inc.empty or bal.empty or cf.empty:
            return None

        # Extract each field, trying multiple possible column names (yfinance inconsistency)
        ni_cur,  ni_pri  = _get(inc, "Net Income", "NetIncome")
        ocf_cur, _       = _get(cf,  "Operating Cash Flow", "Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities")
        icf_cur, _       = _get(cf,  "Investing Cash Flow", "Total Cash From Investing Activities", "Cash Flow From Continuing Investing Activities")
        fcf_cur, _       = _get(cf,  "Financing Cash Flow", "Total Cash From Financing Activities", "Cash Flow From Continuing Financing Activities")
        depr_cur, _      = _get(cf,  "Depreciation And Amortization", "Depreciation", "Depreciation Amortization Depletion")
        sbc_cur,  _      = _get(cf,  "Stock Based Compensation")
        div_cur,  _      = _get(cf,  "Common Stock Dividends Paid", "Dividends Paid")
        re_cur,  re_pri  = _get(bal, "Retained Earnings", "RetainedEarnings")
        cash_cur, _      = _get(bal, "Cash And Cash Equivalents", "Cash", "CashAndCashEquivalents", "Cash Cash Equivalents And Short Term Investments")

        return {
            "ni_cur": ni_cur, "ni_pri": ni_pri,      # Net Income (current + prior)
            "ocf": ocf_cur, "icf": icf_cur, "fcf": fcf_cur,  # Cash flow components
            "depr": depr_cur, "sbc": sbc_cur, "div": div_cur,  # Non-cash + dividends
            "re_cur": re_cur, "re_pri": re_pri,       # Retained Earnings (current + prior)
            "cash_cur": cash_cur,                      # Cash position
        }
    except Exception:
        return None  # yfinance API call failed


@st.cache_data(ttl=3600, show_spinner=False)  # Cache AI analysis for 1 hour
def get_financial_analysis(ticker: str) -> str:
    """Run AI 3-statement analysis for a ticker. Returns the analysis text.

    Returns sentinel strings on failure:
    - '__NO_KEY__' — Groq API key not configured
    - '__NO_DATA__' — yfinance couldn't fetch financial statements
    - '__ERROR__...' — Groq API call failed
    """
    # Get Groq API key from environment or Streamlit secrets
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", None)
    except Exception:
        secret_key = None
    api_key = os.getenv("GROQ_API_KEY") or secret_key
    if not api_key:
        return "__NO_KEY__"  # No API key configured

    # Extract financial data from yfinance
    data = _extract(ticker)
    if data is None:
        return "__NO_DATA__"  # Financial statements not available

    # Calculate derived metrics for the prompt
    ni  = data["ni_cur"]
    ocf = data["ocf"]
    # Cash Conversion Ratio = Operating Cash Flow / Net Income (measures earnings quality)
    ccr_str = (
        f"{float(ocf) / float(ni):.2f}"
        if ni and ocf and float(ni) != 0 else "N/A"
    )
    # Net cash change = OCF + ICF + FCF (should reconcile with balance sheet)
    net_cash = None
    if all(data[k] is not None for k in ["ocf", "icf", "fcf"]):
        net_cash = float(data["ocf"]) + float(data["icf"]) + float(data["fcf"])

    # Build the prompt that instructs the AI to analyse the 3 connections
    prompt = f"""You are an equity analyst. Below are the most recent annual financial figures for {ticker}.

INCOME STATEMENT
{_fmt_m(data['ni_cur'],  'Net Income (current year)')}
{_fmt_m(data['ni_pri'],  'Net Income (prior year)')}
{_fmt_m(data['depr'],    'Depreciation & Amortization')}
{_fmt_m(data['sbc'],     'Stock-Based Compensation')}
{_fmt_m(data['div'],     'Dividends Paid')}

BALANCE SHEET
{_fmt_m(data['re_cur'],  'Retained Earnings (current year)')}
{_fmt_m(data['re_pri'],  'Retained Earnings (prior year)')}
{_fmt_m(data['cash_cur'],'Cash & Equivalents (current year)')}

CASH FLOW STATEMENT
{_fmt_m(data['ocf'],     'Operating Cash Flow')}
{_fmt_m(data['icf'],     'Investing Cash Flow')}
{_fmt_m(data['fcf'],     'Financing Cash Flow')}
Net change in cash: {'${:,.1f}M'.format(net_cash / 1e6) if net_cash is not None else 'N/A'}
Cash conversion ratio (OCF / Net Income): {ccr_str}

Analyse the 3 critical connections between these statements for a retail investor.

CONNECTION 1 — Net Income → Retained Earnings
Show the net income. Calculate the expected change in retained earnings (net income minus dividends). Compare with the actual change. Explain any gap.

CONNECTION 2 — Net Income → Operating Cash Flow
Walk from net income through D&A, stock-based comp, and working-capital changes to arrive at operating cash flow. Comment on whether the cash conversion ratio ({ccr_str}) is healthy or concerning.

CONNECTION 3 — Cash Flow → Cash Position
Show operating CF + investing CF + financing CF = net change in cash. Confirm this reconciles with the balance sheet closing cash.

Then give:
- ONE paragraph on what the 3 connections together reveal about this business's financial health.
- ONE paragraph on whether the 3 statements tell a consistent story, or if anything looks unusual or warrants investor attention.
- Top 3 specific metrics (name + formula) an investor should track across these statements going forward.

If any figure shows 'not available', state this explicitly rather than estimating or inventing a number.

Format: clean sections, numbers first, jargon explained inline. This is educational financial analysis — no buy/sell recommendation."""

    # Call the Groq API with Llama 3.3 70B model
    try:
        client = Groq(api_key=api_key)
        msg = client.chat.completions.create(
            model="llama-3.3-70b-versatile",                # Free-tier model on Groq
            messages=[{"role": "user", "content": prompt}],  # Single-turn analysis
            max_tokens=1400,                                 # ~350 words response limit
        )
        return msg.choices[0].message.content  # Return the AI's analysis text
    except Exception as e:
        return f"__ERROR__{e}"  # API call failed — return error details
