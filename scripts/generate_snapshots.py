"""Batch job: fetch market data and write JSON snapshots for the Next.js site.

This is the data backbone of the Vercel migration (see MIGRATION.md). It runs on a
schedule (GitHub Action, ~every 15 min) — NOT per web request — so the Next.js app
can read pre-computed JSON instantly and never hits Vercel's serverless timeouts.

It deliberately avoids Streamlit: it reuses the pure-pandas math in shared/ but does
its own plain yfinance fetching so it runs anywhere (CI, cron, locally).

Phase 1 scope: pulse.json (marquee + market-card index levels) + meta.json.
Later phases add india.json / us.json (full metrics) and history/<ticker>.json.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# Output dir: the Next.js app serves everything under web/public as static assets.
OUT_DIR = Path(__file__).resolve().parent.parent / "web" / "public" / "data"

IST = timezone(timedelta(hours=5, minutes=30))

# Index tickers shown in the marquee + market cards. Mirrors home.py's pulse list.
# NOTE: index levels are unitless points — never FX-convert them (that was the ~95x
# inflation bug fixed in the Streamlit app). Only stocks/ETFs get USD→INR conversion.
INDIA_INDICES = [
    ("^NSEI", "Nifty 50"),
    ("^BSESN", "Sensex"),
    ("^NSEBANK", "Bank Nifty"),
    ("^CNXIT", "Nifty IT"),
    ("^CNXPHARMA", "Nifty Pharma"),
    ("^NSEMDCP50", "Nifty Midcap 50"),
    ("^CNXAUTO", "Nifty Auto"),
]
US_INDICES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq"),
    ("^DJI", "Dow Jones"),
    ("^RUT", "Russell 2000"),
    ("^SP400", "S&P MidCap 400"),
    ("^VIX", "VIX"),
    ("^FTSE", "FTSE 100"),
]


def _quote(ticker: str) -> dict | None:
    """Fetch latest close + daily % change for one index. None if unavailable."""
    try:
        df = yf.download(ticker, period="7d", interval="1d",
                         auto_adjust=True, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df.get("Close", pd.Series(dtype=float)).dropna()
        if len(close) < 2:
            return None
        cur, prev = float(close.iloc[-1]), float(close.iloc[-2])
        if prev == 0:
            return None
        return {
            "ticker": ticker,
            "price": round(cur, 2),
            "chg": round((cur / prev - 1) * 100, 2),
            "asof": close.index[-1].date().isoformat(),
        }
    except Exception:
        return None


def _usd_inr() -> float:
    """Current USD/INR (for meta + future stock conversion). Falls back to 95.5."""
    try:
        fx = yf.download("USDINR=X", period="5d", progress=False, auto_adjust=True)
        if isinstance(fx.columns, pd.MultiIndex):
            fx.columns = fx.columns.get_level_values(0)
        rate = float(fx["Close"].dropna().iloc[-1])
        if rate > 0:
            return round(rate, 2)
    except Exception:
        pass
    return 95.5


def build_pulse() -> dict:
    """Fetch every marquee/card index and label each row."""
    def rows(defs):
        out = []
        for ticker, label in defs:
            q = _quote(ticker)
            if q:
                out.append({**q, "label": label})
        return out

    return {"india": rows(INDIA_INDICES), "us": rows(US_INDICES)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(IST).strftime("%d %b %Y, %H:%M IST")

    pulse = build_pulse()
    usd_inr = _usd_inr()

    (OUT_DIR / "pulse.json").write_text(json.dumps(
        {"generated_at": generated_at, **pulse}, indent=2))
    (OUT_DIR / "meta.json").write_text(json.dumps({
        "generated_at": generated_at,
        "usd_inr": usd_inr,
        "india_indices": len(pulse["india"]),
        "us_indices": len(pulse["us"]),
    }, indent=2))

    print(f"[snapshots] pulse.json: {len(pulse['india'])} India + "
          f"{len(pulse['us'])} US indices | USD/INR {usd_inr} | {generated_at}")


if __name__ == "__main__":
    main()
