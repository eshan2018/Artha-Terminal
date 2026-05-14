"""Shared display helpers used across all tab modules.

Small utility functions for formatting numbers, picking colors,
building dropdown options, and sanitising user input.
"""
from __future__ import annotations  # Allow modern type hints

import html   # For escaping HTML special characters (XSS prevention)
import math   # For math.isnan() checks
import re     # For regex-based input sanitisation

import pandas as pd  # For DataFrame type hints

# Regex that matches any character NOT allowed in a ticker symbol
# Only uppercase letters, digits, dots, carets, hyphens, and ampersands pass through
SAFE_RE = re.compile(r"[^A-Z0-9.\^\-&]")

# Default Plotly grid styling — subtle grey gridlines, no zero line
_PGRID  = dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)", zeroline=False)

# Default Plotly chart margins (pixels) — tight to maximise chart area
_MARGIN = dict(l=24, r=24, t=36, b=24)


def fmt_pct(v) -> str:
    """Format a number as a percentage string like '+12.34%' or '-5.67%'.
    Returns '—' (em dash) if the value is missing or NaN."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:+.2f}%"  # + sign for positive, - for negative, 2 decimal places


def fmt_num(v, dec: int = 2) -> str:
    """Format a number to a fixed number of decimal places.
    Returns '—' if the value is missing or NaN."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:.{dec}f}"


def chg_color(v) -> str:
    """Return a CSS color variable based on whether a value is positive, negative, or zero.
    Green for gains, red for losses, muted grey for flat or missing."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "var(--text-muted)"  # Grey for missing data
    return "var(--green)" if v > 0 else ("var(--red)" if v < 0 else "var(--text-secondary)")


def arrow(v) -> str:
    """Return an arrow character: ▲ for positive, ▼ for negative, — for zero/missing."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return "▲" if v > 0 else ("▼" if v < 0 else "—")


def asset_options(metrics: pd.DataFrame) -> list[str]:
    """Build a list of 'TICKER — Company Name' strings for dropdown menus."""
    return [f"{r.Ticker} — {r.Name}" for r in metrics.itertuples()]


def ticker_from(opt: str) -> str:
    """Extract the ticker symbol from a 'TICKER — Name' dropdown option."""
    return opt.split(" — ", 1)[0]


def name_from(opt: str) -> str:
    """Extract the company name from a 'TICKER — Name' dropdown option."""
    return opt.split(" — ", 1)[-1]


def safe_ticker(query: str, market: str) -> str:
    """Sanitise user input into a valid ticker symbol.
    Removes all non-alphanumeric characters, uppercases, and auto-appends .NS for Indian stocks."""
    if len(query) > 20:        # Reject suspiciously long input
        return ""
    t = SAFE_RE.sub("", query.upper().strip())  # Remove invalid chars, uppercase
    # For Indian market: append .NS suffix if not an index (^) and no dot present
    if market == "india" and t and not t.startswith("^") and "." not in t:
        t += ".NS"
    return t


def sharpe_stars(v) -> str:
    """Display Sharpe ratio with a star rating for quick visual scanning.
    ★★★ = excellent (≥1.5), ★★ = good (≥0.5), ★ = okay (≥0), ✕ = poor (negative)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if v >= 1.5: return f"★★★  {v:.2f}"   # Excellent risk-adjusted return
    if v >= 0.5: return f"★★    {v:.2f}"   # Good risk-adjusted return
    if v >= 0:   return f"★      {v:.2f}"   # Marginal but positive
    return f"✕       {v:.2f}"               # Negative = losing money vs risk-free


def esc(s: str) -> str:
    """Escape a string for safe HTML rendering — prevents XSS injection."""
    return html.escape(str(s))
