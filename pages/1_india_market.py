"""India Market dashboard page.

Thin entry point — loads the Indian asset universe (110 tickers)
and delegates everything to the shared dashboard orchestrator.
"""
from pathlib import Path
import sys

# Add the project root to Python's module search path
# so we can import from shared/ and tickers/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from shared.dashboard import render_market_dashboard  # Dashboard orchestrator
from tickers import load_universe                     # Loads tickers/india_universe.json

# Render the full India market dashboard with all 7 tabs
render_market_dashboard(
    market="india",                      # Tells data_loader to use NSE primary source
    label="India Market",                # Displayed in page title and header
    universe=load_universe("india"),     # 110 Indian assets (Nifty 100 + ETFs)
)
