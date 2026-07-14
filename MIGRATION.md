# Nivesh Terminal — Streamlit → Vercel Migration

## Why this is a rewrite, not a config change
Streamlit runs a **persistent Python server** with a live WebSocket to the browser;
every interaction re-runs Python server-side. **Vercel is serverless/edge** and cannot
host a Streamlit app. There is no adapter. To live on Vercel the app is rebuilt:
- **UI** (home, dashboards, 7 tabs, charts) → **Next.js (App Router) + React**.
- **Data + math** (yfinance, pandas, Groq) → repurposed as a **scheduled batch job**.

## Chosen architecture: Scheduled Snapshots (everything on Vercel + GitHub)
The app's slow path is fetching 110–220 tickers (~20–30s). Vercel functions time out
at 10s (Hobby) / 60s (Pro) with no warm cache — so we do **not** fetch per request.

```
GitHub Action (cron ~15 min)                Vercel (Next.js)
┌───────────────────────────┐               ┌──────────────────────────┐
│ scripts/generate_         │   commits     │ reads /public/data/*.json│
│ snapshots.py (reuses      │──JSON────────▶│ renders home + dashboards│
│ shared/calculations.py)   │   snapshots   │ (static / ISR, instant)  │
└───────────────────────────┘               └──────────────────────────┘
```
- **Freshness = 15 min**, identical to today's `st.cache_data(ttl=900)`. No regression.
- **Math is reused**: `shared/calculations.py` is pure pandas (no Streamlit) and moves
  into the batch job unchanged. Universes (`tickers/*.json`) reused as-is.
- **Charts**: Plotly.js (same Plotly model as current Python Plotly) to minimise rewrite.
- **AI analysis (Groq)**: short per-request call → a single Vercel serverless function
  (well within limits), or precomputed into snapshots.

## Snapshot files (produced by the batch job → `web/public/data/`)
- `pulse.json` — marquee + market-card index levels (India + US/global indices).
- `india.json` / `us.json` — full metrics table per universe (the Overview + all tabs).
- `history/<ticker>.json` — weekly/daily closes for the Price History & builder charts
  (only what the UI needs; generated per universe).
- `meta.json` — fetched-at timestamp, USD/INR, risk-free rate, counts.

## Phases (Streamlit stays live until the final cutover)
- **P0** Branch + this doc + Next.js skeleton deployed to Vercel (hello world). ← *in progress*
- **P1** Data pipeline: `generate_snapshots.py` + GitHub Action cron. ← *in progress*
- **P2** Home page (hero, marquee, India/US cards) reading `pulse.json`.
- **P3** Market dashboard shell + 7 tabs.
- **P4** Charts (Plotly.js).
- **P5** AI analysis serverless function.
- **P6** Cutover: repoint `niveshterminal.com` → Vercel; decommission Streamlit.

## Repo layout (target)
```
/web            Next.js app (Vercel root)
  /app          routes: /, /india, /us
  /components   marquee, market-card, tabs, charts
  /public/data  JSON snapshots (written by the batch job)
/scripts        generate_snapshots.py (batch job, reuses /shared)
/shared         existing Python math (kept)
/tickers        existing universes (kept)
/deploy/snapshots.workflow.yml     cron template (see activation note below)
```

### Activating the snapshot cron
The workflow lives at `deploy/snapshots.workflow.yml` because pushing files under
`.github/workflows/` requires a token with the `workflow` scope (the automation token
here lacks it). To turn the cron on, **one manual step** — either:
- In GitHub: **Add file → Create new file** at `.github/workflows/snapshots.yml`, paste
  the contents of `deploy/snapshots.workflow.yml`, commit; or
- Grant the PAT the `workflow` scope, then `git mv deploy/snapshots.workflow.yml
  .github/workflows/snapshots.yml` and push.

Until then, snapshots can be regenerated locally: `python scripts/generate_snapshots.py`.
The old Streamlit files (`home.py`, `pages/`, `shared/theme.py`) stay until P6 so the
live site keeps working; they are deleted at cutover.

## Design system carried over
- Accent **amber `#ffb300`**, near-black on amber CTAs, **Inter** titles, dark base
  `#060a12`. Re-expressed as CSS variables / Tailwind tokens in the Next.js app.
