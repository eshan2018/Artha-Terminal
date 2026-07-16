# 08 · Analytics Framework

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review: engine→repository escape hatch closed; `AnalyticResult` ownership moved to doc 04; reference-state pinning (B1); invalidation participation (B4) |
| **Owner** | Quantitative Systems Architect |
| **Depends on** | [04 Canonical Domain Model](04-canonical-domain-model.md), [07 Database Design](07-database-design.md), [16 Data Orchestration & Freshness](16-data-orchestration-and-freshness.md) |
| **Consumed by** | 09, 10, 11, 16 |

## Purpose
Define the common structure that *every* analytics engine obeys — scoring, valuation, risk,
screening, backtesting, portfolio analytics, earnings analysis — so they are uniform,
composable, deterministic, and fully traceable. This is the framework, not the formulas.

## Why it exists
Analytics is where the platform creates value, and where wrong or unexplainable numbers do
the most damage. A shared framework guarantees every engine is reproducible, versioned, and
lineage-emitting *by construction* — and prevents the eleven pillars from becoming eleven
inconsistent silos. It also enforces principle 10: scoring is *one engine here*, not the spine.

## Decisions this document owns

### The two-tier compute model
- **Feature Engineering (L6).** Reusable, named, versioned inputs derived from canonical data:
  returns series, rolling volatility, moving averages, drawdown series, fundamental ratios,
  factor exposures. Features are computed once and shared; engines never re-derive raw inputs
  ad hoc. A feature has: definition, version, inputs (canonical refs), and lineage.
  **Feature-layer ingress is the single, one-way decimal→float seam (audit clarification C3):**
  where a feature consumes decimal monetary Quantities (doc 04) for statistical computation, it
  performs the one deterministic decimal→float conversion here; float values never convert back
  to decimal money. This keeps money exact everywhere except inside statistics, and gives
  parity tests (doc 11) one defined boundary rather than many ad-hoc ones.
- **Analytics Engines (L7).** Consume **features and other engines' results — nothing else**
  (v2.0: the v1.0 "canonical data via repositories where needed" escape hatch is closed; the
  review correctly identified it as the sanctioned reach-around this blueprint exists to
  forbid). If an engine needs canonical data, that need *is* a feature — define it in L6,
  version it, and consume it. Repository access belongs to the feature layer alone. Engines
  never touch providers, raw payloads, or the database (principle 2).

### The engine contract (uniform across all engines)
Every engine, regardless of domain, exposes:
- **Typed inputs** — canonical entities + features + explicit parameters (window, method,
  risk-free source, as-of knowledge_time).
- **A pure, deterministic core** — same inputs + same versions ⇒ same output (principle 11).
  Time and "latest data" are *inputs*, never ambient reads.
- **Versioned methodology** — each formula/method carries a `formula_version`. Changing a
  formula is a new version, never a silent edit; old results remain reproducible.
- **A traced result envelope** — the `AnalyticResult` **whose shape is owned by doc 04**
  (v2.0 ownership resolution): value (typed Quantity, doc 04 numerics), inputs referenced,
  feature versions, formula version, **reference-data/policy snapshot version (B1)**, as-of,
  quality/staleness flags, lineage handle. This document owns how engines *produce* it and may
  not alter its shape. It is the object the API surfaces and the "why?" panel renders. **No
  engine returns a bare number.**

### Determinism, time, and backtest integrity
- **As-of correctness.** Engines read data *as known at* a specified `knowledge_time` (doc 07
  bitemporality). Backtesting is therefore lookahead-free by construction — the framework, not
  engine authors, enforces it.
- **Explicit randomness.** Monte-Carlo methods (e.g. the prototype's 2,000-sim efficient
  frontier) take a seed; results are reproducible and the seed is part of lineage.
- **No silent fabrication (principle 13).** Missing inputs ⇒ the result is `Unavailable` with a
  reason, never a fabricated or zero value.

### Composition & catalog
- **Engines compose via results/features, not by calling each other's internals.** A valuation
  engine may consume a risk feature; it does not import the risk engine's guts.
- **A methodology catalog** documents every feature and formula (definition, version,
  references, assumptions, known limitations). This catalog is user-facing raw material for
  explainability and a compliance artifact (doc 14 — "quantitative, not advice").
- **Materialization vs. on-demand** is a per-engine policy: heavy/shared results are
  pre-computed to the derived-store role (doc 07); light/parameterized ones run on request.
  **Every materialized result registers in the doc 16 dependency graph and declares its
  invalidation policy (`eager`/`next-run`/`on-read`)** — a materialized value that cannot know
  it is stale is forbidden (v2.0, per review B4). Heavy on-demand computations (e.g. seeded
  Monte-Carlo frontiers) run **async with a result handle**, never synchronously inside an API
  request (doc 10).

### The pillars as engines (each a module, none the core)
Fundamentals analysis, valuation, risk analytics, screening (a query engine over
features/results), scoring, portfolio analytics/optimization, earnings analysis, backtesting.
The current `shared/calculations.py` (Sharpe, volatility, returns, MPT frontier, indicators)
is **ported into feature definitions + engine methods behind this contract** — same math,
now versioned, deterministic-by-construction, and lineage-emitting.

## What must NOT live here
- The AI layer that *consumes* these results — doc 09.
- Storage/materialization mechanics — doc 07 (this doc sets policy; doc 07 stores).
- API exposure of results — doc 10.
- Specific numeric formula bodies as *approved production spec* — those live in the versioned
  methodology catalog governed by this framework, added per roadmap phase, not in the blueprint.

## Dependencies
- [04 Canonical Domain Model](04-canonical-domain-model.md) — inputs & the `AnalyticResult` envelope shape.
- [07 Database Design](07-database-design.md) — feature/result materialization + bitemporal reads.

## Completion criteria
- [ ] The engine contract (typed inputs, pure core, versioned methodology, traced envelope) is
      agreed and applies to *every* engine including scoring.
- [ ] Engines consume only features and other engines' results; repository access exists only
      in the feature layer (CI-checkable).
- [ ] Results pin reference-data/policy snapshot versions; materialized results register for
      invalidation (doc 16).
- [ ] Feature layer is defined as versioned, reusable, and lineage-carrying.
- [ ] As-of / lookahead-free evaluation is guaranteed by the framework, not engine authors.
- [ ] Determinism (incl. seeded randomness) is mandated and testable (doc 11).
- [ ] A methodology catalog exists as the home for formulas + limitations.
- [ ] Removing the scoring engine leaves the framework and other engines intact.
