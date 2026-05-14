"""US Market dashboard page.

Thin entry point — loads the US asset universe (110 tickers)
and delegates everything to the shared dashboard orchestrator.
"""
from pathlib import Path
import sys

# Add the project root to Python's module search path
# so we can import from shared/ and tickers/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from shared.dashboard import render_market_dashboard  # Dashboard orchestrator
from tickers import load_universe                     # Loads tickers/us_universe.json

# Render the full US market dashboard with all 7 tabs
render_market_dashboard(
    market="us",                        # Tells data_loader to use yfinance batch path
    label="US Market",                  # Displayed in page title and header
    universe=load_universe("us"),       # 110 US assets (S&P 500 + ETFs)
)
