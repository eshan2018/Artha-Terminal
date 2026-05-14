# Artha Terminal 🇮🇳📊

**A full-stack financial intelligence dashboard for Indian and US markets** — built with Python, Streamlit, and real-time market data APIs.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What it does

Artha Terminal tracks **220 assets** across Indian (Nifty 100 + NSE ETFs) and US markets, providing a 20-year historical view with institutional-grade analytics:

| Feature | Details |
|---------|---------|
| **Market Overview** | Live price table with 1D/1W/1M/1Y/3Y returns, Sharpe rating, volatility, market cap |
| **Portfolio Builder** | Percentile-rank stock recommender · What-If projector with ±1σ confidence cone · Goal reverse-calculator |
| **Search & Intel** | Per-ticker intelligence card: returns, dual volatility (long-term + 1M), Sharpe, RSI, 52W stats + AI 3-statement analysis |
| **Performance Heatmap** | Treemap, sector sunburst, calendar heatmap · Top 5 gainers/decliners |
| **Price History** | Interactive chart with SMA/EMA/Bollinger overlays + RSI/MACD sub-charts |
| **Risk vs Return** | Scatter plot with Security Market Line + drawdown panel |
| **Glossary** | Searchable financial terms with live Sharpe playground |

---

## Financial math highlights

- **Sharpe ratio** — numerator is `mean(weekly_returns) × 52`, not point-in-time 1Y return. More statistically robust for trending assets.
- **Risk-free rate** — fetched live from India's 10Y G-Sec yield (`^INBMK`), 6.5% fallback if unavailable.
- **Dual volatility** — `weekly × √52` for long-term horizon; `daily × √252` for 1-month holding period.
- **Portfolio variance** — uses full covariance matrix (`w @ Σ @ w`), not the zero-correlation approximation.
- **Efficient Frontier** — 2,000-simulation Monte Carlo with annualised covariance.
- **Returns** — calendar-accurate `pd.DateOffset` matching with 30-day tolerance, not hardcoded day counts.

---

## Run locally

```bash
# 1. Clone
git clone https://github.com/<your-username>/artha-terminal.git
cd artha-terminal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add API keys
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml and add your GROQ_API_KEY

# 4. Launch
streamlit run home.py
```

> **Python 3.12 required.** Dependencies are version-pinned in `requirements.txt`.

---

## Project structure

```
artha-terminal/
├── home.py                    # Landing page with live market pulse
├── pages/
│   ├── 1_india_market.py      # India dashboard (Nifty 100 + ETFs)
│   └── 2_us_market.py         # US dashboard (S&P 500 + ETFs)
├── shared/
│   ├── dashboard.py           # Orchestrator: data loading + tab dispatch
│   ├── calculations.py        # All financial math (Sharpe, vol, returns, SIP, MPT)
│   ├── data_loader.py         # Cached data fetching (yfinance, NSE, Alpha Vantage)
│   ├── ai_analysis.py         # Groq/Llama 3.3 70B financial statement analysis
│   ├── theme.py               # Design system + CSS tokens
│   └── tabs/                  # One file per dashboard tab
│       ├── tab_overview.py
│       ├── tab_builder.py
│       ├── tab_search.py
│       ├── tab_heatmap.py
│       ├── tab_charts.py
│       ├── tab_risk.py
│       └── tab_glossary.py
└── tickers/
    ├── india_universe.json    # 110 Indian assets (editable without touching code)
    └── us_universe.json       # 110 US assets
```

---

## Data sources

| Source | Used for |
|--------|---------|
| **yfinance** | US equities, indices, ETFs, USD/INR FX, India 10Y G-Sec yield |
| **NSE (jugaad-data / nsepython)** | Indian equity primary source |
| **Alpha Vantage** | US equities fallback |
| **Groq (Llama 3.3 70B)** | AI financial statement analysis |

---

## Configuration

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_..."           # Free at console.groq.com
ALPHA_VANTAGE_API_KEY = "..."      # Free at alphavantage.co
```

---

## Disclaimer

> Artha Terminal is an educational tool. All signals are quantitative and do not constitute investment advice. Past performance does not guarantee future results. Consult a SEBI-registered investment advisor before making financial decisions.

---

## License

MIT © 2026 Eshan Mandloi
