# 04 · Canonical Domain Model

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B1 (versioned reference data), B5 (numerics), B6 (scoped temporality), B8 (authority tiers); `AnalyticResult` ownership resolved |
| **Owner** | Principal Data Architect |
| **Depends on** | [03 System Architecture](03-system-architecture.md) |
| **Consumed by** | 05, 06, 07, 08, 09, 10, 14, 16, 17 |

## Purpose
Define the **shared vocabulary** of the platform: the vendor-neutral entities, identifiers,
relationships, and units that every layer above normalization speaks. This is the "ubiquitous
language" of the whole system.

## Why it exists
If each provider's shape leaks upward, every analytic and API is coupled to vendors and
principle 7 (replaceability) is dead. The canonical model is the *lingua franca* into which
all vendor data is translated once, so everything above it is vendor-agnostic and stable.

## Decisions this document owns

### Identity — the hardest and most important decision
- **Nivesh assigns its own internal identifiers.** No vendor ID (yfinance ticker, Alpha
  Vantage symbol, ISIN, CUSIP) is ever a primary key in the domain. Vendor identifiers are
  *cross-reference attributes*, not identity.
- **`InstrumentId`** is the internal stable key for a tradable/observable instrument. It maps
  to many external identifiers via a **symbology/cross-reference table** (ISIN, MIC-qualified
  ticker, vendor symbols). This is the single place ticker-collisions (RELIANCE.NS vs a US
  RELIANCE, `^NSEI` index vs equity) are resolved.
- **Market context is explicit.** An instrument trades on a venue (MIC), in a currency, in a
  country. `TSLA` is not a bare string; it is (Instrument, Exchange, Currency).

### Core entities (definitions, not schemas — schemas are doc 07)
- **Instrument** — anything with observable market data: equity, ETF, index, FX pair, bond,
  rate. Carries `InstrumentType` so units and valid analytics are known (e.g. *index levels
  are unitless points and must never be FX-converted* — a bug the prototype fixed; the model
  makes it type-impossible).
- **Company / Issuer** — the economic entity behind fundamentals; one issuer ↦ many
  instruments (share classes, listings). Fundamentals attach to Company, prices to Instrument.
- **Exchange / Venue** — MIC, timezone, trading calendar, settlement conventions.
- **PriceObservation** — OHLCV (+ adjusted) for an Instrument at an interval, with the
  event-time bar timestamp *and* the knowledge-time we learned it.
- **CorporateAction** — splits, dividends, and the adjustment factors that make price series
  continuous; first-class so adjustment is auditable, never hidden.
- **FundamentalFact** — a single line item (revenue, EPS, …) for a Company, for a fiscal
  period, on a reporting basis (restated vs. as-reported), with statement + taxonomy tag.
- **FiscalPeriod** — period end, fiscal-year alignment, quarter/annual, restatement lineage.
- **EconomicSeries / EconomicObservation** — macro series (rates, CPI, G-Sec yield) as
  first-class data, not constants buried in code (the prototype's live risk-free rate becomes
  an `EconomicSeries`).
- **FXRate** — currency pair observations; the *only* sanctioned source of conversion factors.
- **Universe** — a named, versioned set of instruments (Nifty 100, S&P 500, a user watchlist).
  Universes are data, editable without code (seeded from `tickers/*_universe.json`).
- **DerivedValue / AnalyticResult** — the canonical envelope every analytic emits: value,
  unit, inputs referenced, formula id + version, reference-data snapshot version, quality/
  staleness flags, and lineage handle. **Ownership (v2.0, resolving the review's co-ownership
  finding): this document owns the envelope's shape as a canonical entity; doc 08 owns how
  engines produce it and may not alter the shape.** Uniform lineage platform-wide depends on
  single ownership.
- **Provenance / Lineage** — for any fact or derived value: which provider, which raw record,
  which transformation version produced it. A cross-cutting relationship, not an afterthought.

### Cross-cutting modeling rules
- **Units and currency are always explicit** on any quantity, carried by a shared **Quantity
  value type** (value + unit + currency where applicable). No bare numbers crossing a layer
  boundary. Money carries currency; ratios carry none; index levels carry "points."
- **Numerics are typed (v2.0, per review B5 / principle 19):** monetary quantities are
  **decimal** with per-currency precision and declared rounding; statistical quantities
  (returns, volatilities, ratios, simulation outputs) may be floating point. The Quantity
  type makes float-money unrepresentable, not merely discouraged. **The decimal→float seam is
  one-way and singular (audit clarification C3):** money is decimal at rest, in the domain,
  and at the API; a single deterministic decimal→float conversion is permitted only at
  feature-layer ingress for statistical computation (doc 08); float→decimal reverse conversion
  is forbidden.
- **Temporality is scoped per data class (v2.0, per review B6)** via a **temporal-policy
  matrix** owned jointly with doc 07:
  - **Fully bitemporal** (`event_time` + `knowledge_time`, as-of queries): fundamentals and
    economic observations — restatement-heavy classes where "what did we know when?" is the
    product.
  - **Effective-dated with versioned corrections**: prices, FX, reference data — corrections
    create new versions with timestamps, but full as-of query machinery is deferred until
    Phase 6 backtesting requires it (doc 15 gate). **`knowledge_time` is populated on every
    ingestion from the first Phase 0.5 row (audit clarification C1)** — only the as-of *query
    machinery* is deferred, never the timestamp itself; ingestion time is free to capture and
    impossible to backfill, so the upgrade is additive, not a migration.
  Blanket bitemporality-everywhere was a v1.0 overreach; honest backtests need it where
  restatements happen, not on every read path.
- **Reference data is effective-dated, versioned data (v2.0, per review B1).** Symbology
  mappings, trading calendars, corporate actions, FX sources, and source-priority /
  entitlement policies all carry validity intervals and version identity — so any computation
  can pin, and later reproduce, the exact reference state it used (lineage tiers, principle 6).
- **Facts carry an authority tier (v2.0, per review B8):** `authoritative` (passed the doc 05
  gate from a trusted source) or `candidate` (e.g. AI-extracted, single-source-unconfirmed).
  Candidate facts are never served as authoritative and never feed authoritative analytics;
  promotion rules live in docs 05/09.
- **Restatements and corrections are new versions**, linked to what they supersede; nothing
  is overwritten (within the doc 17 lifecycle).
- **The model does not privilege scoring.** A `Score` is just one `AnalyticResult` type;
  removing scoring must not perturb any core entity (principle 10).

## What must NOT live here
- Physical storage (tables, indexes, partitioning) — doc 07.
- Vendor field names or quirks — those are mapped *into* this model by adapters (doc 06).
- Formulas or feature definitions — docs 06/08.
- API serialization / DTO shapes — doc 10 (the API is a *projection* of this model, not the
  model itself).

## Dependencies
- [03 System Architecture](03-system-architecture.md) — this model is L4/L5's contract.
- Consumed by every layer above normalization; it is the platform's contract spine.

## Completion criteria
- [ ] Identity strategy (internal IDs + symbology cross-reference) is agreed; no vendor ID is
      a primary key anywhere.
- [ ] Every entity has explicit units/currency via the Quantity type; money is decimal-only.
- [ ] The temporal-policy matrix assigns every fact class its temporality tier, with the
      bitemporal upgrade path reserved in-schema.
- [ ] Reference data and policies are effective-dated and versioned.
- [ ] Candidate vs. authoritative tiers exist and candidate data is unservable as authoritative.
- [ ] The model can represent every data class the eleven pillars (doc 01) require, and the
      current prototype's data, without a vendor-shaped field.
- [ ] "Delete scoring" is a no-op on core entities.
- [ ] Docs 05, 06, 07, 08, 10 can each be written referencing only this vocabulary.
