"""Universe loader — reads from JSON files so tickers can be updated
without touching Python source code."""
from __future__ import annotations  # Allow modern type hints in older Python

import json            # For reading JSON files
from pathlib import Path  # For cross-platform file path handling

# Directory where this file lives (tickers/)
_DIR = Path(__file__).parent


def load_universe(market: str) -> list[dict]:
    """Load asset universe from tickers/<market>_universe.json.

    Falls back to the legacy Python module if the JSON file is absent,
    so old deployments keep working during a migration.
    """
    # Build path like tickers/india_universe.json or tickers/us_universe.json
    json_path = _DIR / f"{market}_universe.json"

    # If JSON file exists, load and return it directly
    if json_path.exists():
        with open(json_path, encoding="utf-8") as fh:
            return json.load(fh)

    # Legacy fallback — import from old Python module if JSON not found
    if market == "india":
        from tickers.india_universe import INDIA_UNIVERSE
        return INDIA_UNIVERSE
    if market == "us":
        from tickers.us_universe import US_UNIVERSE
        return US_UNIVERSE

    # Unknown market name — raise an error
    raise ValueError(f"Unknown market: {market!r}")
