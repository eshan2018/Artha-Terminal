# 06 · Provider Abstraction Layer

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B6 (router deferred), B9 (license metadata feeds doc 17); raw-contract versioning added |
| **Owner** | Chief Software Architect |
| **Depends on** | [04 Canonical Domain Model](04-canonical-domain-model.md), [05 Market Data Architecture](05-market-data-architecture.md) |
| **Consumed by** | 05 (stage 1), 07, 14, 15 |

## Purpose
Define the port/adapter contract that makes **every provider replaceable** (principle 7) and
**vendor lock-in minimal** (principle 8). This is the quarantine zone where — and *only*
where — vendor-specific knowledge is allowed to exist.

## Why it exists
The prototype's `data_loader.py` interleaves yfinance, NSE, and Alpha Vantage quirks with
business logic. That is exactly the coupling this layer abolishes. If a vendor changes terms,
raises prices, degrades quality, or dies, we swap an adapter — nothing above L1 notices.

## Decisions this document owns

### The port/adapter pattern (hexagonal)
- **Ports** are Nivesh-defined interfaces expressing *what the platform needs*, in canonical
  terms (doc 04): e.g. `PriceHistoryPort`, `FundamentalsPort`, `CorporateActionsPort`,
  `FxRatePort`, `EconomicSeriesPort`, `SecurityReferencePort`, `NewsPort`.
- **Adapters** implement a port for one vendor. All vendor knowledge — auth, base URLs,
  pagination, rate limits, retries/backoff, field names, quirks, error mapping — lives *inside*
  the adapter and nowhere else.
- **The contract is bidirectional and canonical.** Inputs are canonical requests
  (`InstrumentId` + market context, not vendor tickers — the adapter resolves symbology).
  Outputs are canonical-shaped results (or the raw payload for L2 capture) — never leaked
  vendor DTOs.

### What a port contract must specify
- **Capabilities** — which instrument types, markets, intervals, history depth, and fields the
  adapter supports (so the router knows who can serve a request).
- **Freshness & latency characteristics** — for SLA and source-priority decisions (doc 05).
- **Error taxonomy** — mapped to a common set: `NotAvailable`, `RateLimited`, `AuthFailed`,
  `Malformed`, `Transient`. Callers handle the taxonomy, never vendor-specific errors.
- **Rate-limit & quota semantics** — declared, so the platform schedules within them.
- **Licensing metadata** — each adapter declares the licensing/redistribution terms of its
  data: may we store it? serve it? for how long? to whom? derived-only? attribution required?
  These declarations are the machine-readable input to the **entitlements engine (doc 17)**;
  doc 14 rules on their interpretation.
- **A versioned raw-payload contract (v2.0, new).** Each adapter declares the shape it
  expects from the vendor as a versioned contract and detects drift: when a vendor silently
  changes its payload (new/renamed fields, changed semantics), the mismatch surfaces as a
  `Malformed`-class event and affected fetches quarantine — instead of normalization quietly
  producing subtly wrong canonical data. Vendor payload drift is a *when*, not an *if*.

### Cross-cutting adapter responsibilities (provided by the layer, not each adapter)
- **Symbology resolution** — canonical `InstrumentId` ↔ vendor symbol, via the cross-reference
  table (doc 04). Adapters never invent identity.
- **Resilience** — retry/backoff, circuit-breaking, and timeout policy standardized around the
  common error taxonomy.
- **Raw capture hook** — every successful fetch hands its verbatim payload + metadata to the
  Raw Store (doc 05 stage 2) before normalization.
- **Provider registry & routing — designed as a slot, built when needed (v2.0, per review
  B6/principle 18).** Until a second provider per port exists, resolution is trivial (one
  adapter per port) and no router is built. The *contract* reserves the seam: requests are
  already canonical and capability-declared, so introducing the router — capability-based
  selection, source-priority failover, multi-source corroboration — at the second-provider
  phase (doc 15 Phase 5) is additive. Building it earlier is speculative machinery with no
  second source to route to.

### Provider governance decisions
- **No vendor name appears above L1.** Enforced by dependency linting (doc 03/11): the string
  "yfinance"/"alphavantage"/etc. is a build failure outside the adapters package.
- **Adapters are independently testable** against recorded fixtures (contract tests, doc 11),
  so a new provider is proven to satisfy a port before it is trusted.
- **Adding/removing a provider is an adapter-level change** with zero edits above L1 — this is
  the acceptance test for the whole layer.

### Migration of existing sources
`yfinance`, NSE, and Alpha Vantage each become an adapter behind the relevant ports; Groq is
*not* a data provider (it's AI infra — doc 09). The prototype's batch fetch, FX handling, and
NSE-symbol mapping become adapter internals, cleaned up to the contract.

## What must NOT live here
- The pipeline stages that *consume* adapters (validation/normalization) — doc 05.
- Canonical entity definitions — doc 04 (this layer targets them).
- Storage of raw/canonical data — doc 07.
- The *decision* of what we're licensed to do — doc 14 (adapters *declare* terms; doc 14
  *rules* on them).

## Dependencies
- [04 Canonical Domain Model](04-canonical-domain-model.md) — the language of ports.
- [05 Market Data Architecture](05-market-data-architecture.md) — the consumer of adapters.
- [14 Compliance & Licensing](14-compliance-and-licensing.md) — consumes adapter license metadata.

## Completion criteria
- [ ] Port interfaces are enumerated and expressed purely in canonical terms.
- [ ] "Swap/add a provider with zero changes above L1" is a written, testable acceptance criterion.
- [ ] Common error taxonomy, capability declaration, licensing metadata fields (consumable by
      doc 17), and the versioned raw-payload contract are defined.
- [ ] The router seam is specified as deferred: one-adapter-per-port until Phase 5, with the
      contract proven additive for routing/failover/corroboration.
- [ ] Dependency-lint rule banning vendor names above L1 is defined for CI.
