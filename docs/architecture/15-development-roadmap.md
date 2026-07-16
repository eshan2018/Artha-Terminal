# 15 · Development Roadmap

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blocker B12 (walking skeleton + strangler) and deferral gates (B6); orchestrator + hosting + governance sequenced |
| **Owner** | Chief Software Architect / FinTech CTO |
| **Depends on** | 01–17 (sequences the whole set) |
| **Consumed by** | Engineering execution |

## Purpose
Determine the **correct order of construction** so the platform is built foundation-first,
minimizing technical debt and avoiding premature optimization. Each phase states its
objective, deliverables, dependencies, success criteria, and — critically — **what must NOT
be built yet**.

## Why it exists
The right architecture built in the wrong order still produces debt: an API before a domain
model bakes in vendor shapes; analytics before lineage produce untraceable numbers; AI before
analytics hallucinates. This roadmap enforces the layered invariant *in time*, not just in
structure.

## Sequencing principles
1. **Build bottom-up along the stack (doc 03).** A layer is built only after the layer it
   depends on is real and tested.
2. **Make it traceable before you make it fast** (principle 11/18) — lineage and correctness
   precede performance and scale.
3. **One vertical slice at a time.** Prove the whole stack on a *narrow* data scope (a handful
   of instruments) before widening — depth before breadth.
4. **Widening the universe is a data-ops task, not an architecture change.** If adding
   instruments requires code changes above the adapter, the architecture failed.
5. **Defer distribution, streaming, and optimization until a phase's success criteria demand
   them.** Premature scale is debt. Heavier machinery (router, TSDB, event backbone, full
   price bitemporality) is introduced only through the **written escalation gates** of docs
   06/07 (v2.0).
6. **Continuous value via the strangler pattern (v2.0, per review B12).** The existing
   Streamlit/Next.js prototype **stays live as the product** throughout; real endpoints
   replace snapshot JSON surface-by-surface. Users never wait for the foundation — v1.0's
   "zero user value until Phase 4" was a business risk, not discipline.

---

## Phase 0 — Blueprint approval & guardrails
- **Objective:** Freeze the architecture and stand up the mechanisms that *enforce* it before
  any feature code.
- **Deliverables:** This doc set approved (statuses → Approved); repository restructured to the
  layer packages of doc 03 with module-owned schema boundaries; **dependency-direction
  linting** + **no-vendor-name-above-L1** + **no-cross-module-table-access** lint in CI
  (docs 03/06/07/11); CI skeleton running the (initially tiny) test suites; the methodology
  catalog and decision-log conventions (docs 02/08) in place.
- **Dependencies:** Docs 01–17.
- **Success criteria:** An "upward import," a leaked vendor string, or a cross-module table
  read fails CI. Every planned module maps to exactly one owning document.
- **Do NOT build yet:** Any provider adapter, database, analytics, API, or UI feature.

## Phase 0.5 — Walking skeleton (v2.0, per review B12)
- **Objective:** De-risk the *entire* stack with the thinnest possible end-to-end slice before
  broad foundation investment — weeks, not months.
- **Deliverables:** **5 instruments, 1 provider (yfinance adapter), 1 metric (e.g. 1Y
  return)**, flowing adapter → raw capture → validation → normalization → domain store
  (managed Postgres + object storage, doc 07 minimal schemas) → 1 feature → 1 engine →
  **one minimal typed v1 endpoint** → rendered by the existing Next.js frontend alongside its
  current snapshot data. A minimal DAG on the managed orchestrator (doc 16). **Time the
  recompute-from-raw path** (doc 12 RTO evidence).
- **Dependencies:** Phase 0.
- **Success criteria:** Every layer exists and is exercised once; lineage resolves end-to-end
  for the one metric; the recompute timing number exists; the strangler pattern is proven (one
  real endpoint live next to snapshot JSON without breaking the site).
- **Do NOT build yet:** More instruments, more metrics, more endpoints, any breadth at all —
  the skeleton's only job is proving the bones connect.

## Phase 1 — Canonical domain model + reference/master data
- **Objective:** Establish the platform vocabulary and identity system (doc 04) as code +
  schema, seeded from existing universes.
- **Deliverables:** Canonical entities (Instrument, Company, Exchange, PriceObservation,
  FundamentalFact, CorporateAction, EconomicSeries, FXRate, Universe, `AnalyticResult`
  envelope, Provenance) with typed Quantities (decimal money, doc 04), authority tiers, and
  the temporal-policy matrix applied; **effective-dated reference data**; the
  **symbology/cross-reference** + internal-ID system; reference/master schemas in the doc 07
  two-store layout; `tickers/*_universe.json` migrated into seeded universes with internal IDs.
- **Dependencies:** Phase 0.5 (hardens the skeleton's provisional model).
- **Success criteria:** A ticker collision (e.g. index vs. equity, `.NS` vs US symbol) resolves
  to distinct internal IDs; units/currency/bitemporal fields exist on every fact type; "delete
  scoring" is a no-op on the model.
- **Do NOT build yet:** Time-series at scale, analytics, providers beyond a stub, any API.

## Phase 2 — Provider abstraction + ingestion of ONE data class, end-to-end
- **Objective:** Prove the full ingestion pipeline (doc 05) through the port/adapter contract
  (doc 06) for **EOD equity prices only**, on a **small instrument set**.
- **Deliverables:** `PriceHistoryPort` + one adapter (yfinance, cleaned from the prototype's
  `data_loader.py`, with a versioned raw-payload contract); raw capture (immutable within
  lifecycle); validation gate + quarantine + authority stamping; normalization with **pinned
  reference-data versions** to `PriceObservation` (effective-dated, corporate-action-aware);
  time-series/fundamentals schemas in the two-store layout (doc 07); **production DAGs on the
  orchestrator with idempotent tasks, backfill, and the first invalidation wiring —
  corporate-action reprocessing** (doc 16); adapter contract tests on fixtures (doc 11).
- **Dependencies:** Phases 0–1 (walking skeleton components hardened, not rebuilt).
- **Success criteria:** Prices for the small set flow raw→validate→normalize→persist with full
  lineage resolvable to raw records *and* reference versions; bad data quarantines (never
  mutates); a corporate-action correction cascades correctly; recompute-from-raw works within
  its measured time; **no vendor name exists above L1**.
- **Do NOT build yet:** A second provider or any router, fundamentals/economics ingestion,
  streaming, the full 220-asset universe, analytics beyond a trivial smoke test, API breadth.

## Phase 3 — Feature engineering + first analytics engines (behind the framework)
- **Objective:** Port the prototype's math into the doc-08 framework: versioned features +
  deterministic, traced engines — starting with returns/volatility/Sharpe and one
  multi-input engine (portfolio/MPT).
- **Deliverables:** Feature layer (returns, rolling vol, drawdown, ratios) as versioned
  definitions — **the only layer with repository access** (doc 08 v2.0); engines emitting
  `AnalyticResult` envelopes with lineage + formula + reference-snapshot versions;
  materialized results registered in the doc 16 dependency graph with declared invalidation
  policies; seeded-determinism for Monte-Carlo (frontier); **property-based tests + an
  independent reference implementation per engine**, goldens seeded only after parity
  (doc 11 v2.0).
- **Dependencies:** Phase 2 (needs real canonical data).
- **Success criteria:** Every metric is reproducible and traces to inputs + formula +
  reference versions; a stale input flags its dependents; changing a formula requires a
  version bump; parity holds within the tolerance policy.
- **Do NOT build yet:** AI, the API, screening/valuation/backtest breadth, performance tuning.

## Phase 4 — Read/analytics API (v1) + frontend cutover
- **Objective:** Expose canonical data + traced analytics through the versioned REST contract
  (doc 10) and migrate the Next.js frontend off static JSON onto v1.
- **Deliverables:** OpenAPI-first v1 (securities, prices, analytics endpoints) as DTO
  projections (not table dumps); lineage/"why?" + freshness/staleness metadata per derived
  value; `as_of` querying where the temporal matrix supports it; **the API's backend-cloud
  hosting stood up** (containers — not serverless edge; doc 12 v2.0); edge auth scaffolding,
  rate limiting, and the **entitlements engine in its simplest configuration** (single public
  tier, per-source flags — the abstraction, not the tiers; doc 17); frontend migrates
  surface-by-surface (strangler); contract tests.
- **Dependencies:** Phase 3.
- **Success criteria:** Frontend renders migrated surfaces from v1 with freshness + lineage
  surfaced; an internal storage refactor does not break clients; snapshot JSON is retired
  per-surface as endpoints replace it.
- **Do NOT build yet:** AI endpoints, write/user features (portfolios/workspaces), multi-tenant
  auth depth, heavy caching/scaling beyond correctness.

## Phase 5 — Broaden data: universe scale-up + second provider + more data classes
- **Objective:** Widen coverage as a *data-ops* activity: full India+US universes, a second
  price adapter (failover/reconciliation), and fundamentals + economics ingestion.
- **Deliverables:** Second `PriceHistoryPort` adapter — and with it, **now and only now, the
  provider registry/router, failover, and source-priority reconciliation** (docs 05/06 v2.0
  deferral gates open here); `FundamentalsPort` + `EconomicSeriesPort` adapters and pipelines;
  the prototype's live risk-free rate becomes an `EconomicSeries`; data-quality monitoring
  dashboards with SLO thresholds (docs 11/12).
- **Dependencies:** Phase 4 (stable stack to widen).
- **Success criteria:** Adding instruments/sources touches only data + adapters, never layers
  above L1; cross-source disagreements are recorded as lineage; freshness/quality alerting live.
- **Do NOT build yet:** Streaming/intraday, AI, advanced analytics breadth still optional.

## Phase 6 — Analytics breadth: valuation, risk, screening, earnings, backtesting
- **Objective:** Build out the pillar engines (doc 08) now that broad, trusted data exists —
  each as a module on the common framework, none privileged.
- **Deliverables:** Valuation, risk analytics, screening (query engine over features/results),
  earnings analysis, backtesting — **this phase opens the temporal gate: prices upgrade from
  effective-dated to full bitemporal as-of reads** (the doc 04/07 reserved upgrade), because
  honest backtesting is the constraint that justifies it; methodology-catalog entries +
  property/reference tests per engine; API exposure per doc 10 (heavy runs async).
- **Dependencies:** Phase 5 (broad data), Phase 4 (API pattern).
- **Success criteria:** Each engine is traced, versioned, deterministic; backtests provably
  lookahead-free; screening is just a query surface, scoring just one engine.
- **Do NOT build yet:** AI research features until the analytics substrate they cite exists
  (this phase creates it).

## Phase 7 — AI layer (grounded, cited, guard-railed)
- **Objective:** Add the AI framework (doc 09) strictly on top of analytics: retrieval over the
  platform's own facts/results, cited narrative generation, research assistant — with the
  no-advice boundary and injection defenses enforced.
- **Deliverables:** AI provider port + adapter (Groq/Llama or other, swappable behind the
  eval gate); RAG over the **phase-1 corpus only** — canonical facts + `AnalyticResult`s +
  methodology catalog (filings/news ingestion is a separately scoped later programme, doc 09
  v2.0); defense-in-depth grounding (construction + provenance + faithfulness checks +
  labeling) with a residual-risk register; no-advice guardrail; prompt-injection defenses
  (doc 13); per-surface budgets + circuit-breakers; AI eval suite w/ thresholds (doc 11);
  AI API endpoints (doc 10), entitlement-aware (doc 17).
- **Dependencies:** Phase 6 (the factual substrate to cite).
- **Success criteria:** Eval-suite thresholds pass (grounding, faithfulness, no-advice,
  injection); every AI statement carries provenance and labeling; model swap is demonstrated
  behind the eval gate; budgets enforce.
- **Do NOT build yet:** Autonomous/agentic actions, personalized recommendations (out of scope
  by doc 01/14), filings/news RAG corpus (own programme, own gate).

## Phase 8 — User features, hardening, and commercial-readiness
- **Objective:** Add authenticated user surfaces (watchlists, portfolios, research workspaces),
  and close the operational/compliance gaps for real users.
- **Deliverables:** AuthN/Z + tenant isolation (doc 13); user-data stores (encrypted under
  per-user crypto scopes, segregated — doc 17 lifecycle live, **DSR access/erasure exercised
  end-to-end**); write endpoints (idempotent, doc 10); **entitlements engine in full
  configuration** (real tiers × licensed sources — configuration, not surgery, because the
  abstraction shipped in Phase 4); systematic disclosures/AI-labeling (doc 14); full
  observability, backup + recompute recovery drills, chaos tier, progressive delivery
  (docs 11/12); **commercial-grade licensed data feeds** swapped in behind existing adapters,
  and the "decide-with-counsel" compliance items (incl. DPDP localization) resolved (doc 14).
- **Dependencies:** Phases 4–7.
- **Success criteria:** A user completes a real research question end-to-end and can audit every
  input (doc 01 success definition); security/isolation verified; licensing + disclosures fit
  for commercial operation; recovery paths exercised.
- **Do NOT build yet (still deferred until demanded):** Service extraction from the modular
  monolith, streaming/intraday infrastructure, event backbone, aggressive performance
  optimization — each introduced only when a measured constraint forces it (principle 18).

---

## What this roadmap deliberately refuses to do early
- **No API before a domain model** (Phase 4 after 1–3) — prevents baking vendor shapes into the
  contract. (The Phase 0.5 skeleton endpoint is a deliberate, disposable exception scoped to
  one metric — its job is proving the seams, and it is re-cut on the hardened model.)
- **No analytics before lineage** (Phase 3 after 2) — prevents untraceable numbers.
- **No AI before analytics** (Phase 7 after 6) — prevents hallucination; AI must cite real results.
- **No breadth before a proven vertical slice** (Phase 5 after 4) — depth first.
- **No router before a second provider; no TSDB/graph/event-backbone/cache tier before its
  doc 07 gate; no full price bitemporality before backtesting** (v2.0 deferral gates).
- **No dark-months foundation work** — the walking skeleton + strangler keep the live product
  improving continuously (v2.0).
- **No distribution/streaming/optimization on spec** — only when a phase's success criteria require it.
- **No commercial launch on hobby data feeds** — licensing gate at Phase 8 (doc 14).

## Completion criteria (for the roadmap itself)
- [ ] Every phase has objective, deliverables, dependencies, success criteria, and explicit non-goals.
- [ ] The order honors the layered dependency invariant (doc 02/03) with no forward reference.
- [ ] Each "do NOT build yet" is justified by debt-avoidance, not indecision.
- [ ] Phase success criteria are objectively testable via doc 11.
