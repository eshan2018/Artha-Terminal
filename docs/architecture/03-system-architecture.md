# 03 · System Architecture

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B3 (orchestration), B7 (integration model), B1 (recompute claim qualified) |
| **Owner** | Chief Software Architect |
| **Depends on** | [01 Vision](01-vision.md), [02 Engineering Principles](02-engineering-principles.md) |
| **Consumed by** | 04–17 |

## Purpose
Define the platform's structural decomposition: the layers, the boundaries between them, how
data flows, and the runtime shape (services, jobs, stores) — at the level of *architecture*,
not implementation.

## Why it exists
The layered dependency invariant (doc 02) is only real if the system is physically organized
to enforce it. This document maps the abstract stack onto concrete, bounded components with
owned contracts, so that "nothing bypasses the architecture" is a structural fact.

## Decisions this document owns

### The layer stack (the invariant, concretized)
Each layer exposes a contract *downward-consumers* use and hides its internals. A layer may
call only the published contract of the layer directly beneath it.

| Layer | Responsibility | Contract it publishes | May depend on |
|-------|----------------|-----------------------|---------------|
| **L0 Providers** | External data vendors | (vendor APIs — outside our trust boundary) | — |
| **L1 Provider Adapters** | Translate one vendor ↔ our ports | `ProviderPort` interfaces (doc 06) | L0 only |
| **L2 Raw Store** | Verbatim capture of vendor payloads | Immutable raw records + fetch metadata | L1 |
| **L3 Validation** | Gate: schema/range/consistency checks | Accepted / quarantined verdicts (doc 05) | L2 |
| **L4 Normalization** | Vendor shapes → canonical shapes | Canonical entities (doc 04) | L3 |
| **L5 Domain Store (DB)** | System of record + lineage | Repository interfaces over canonical model | L4 |
| **L6 Feature Engineering** | Reusable analytic inputs | Named, versioned feature definitions | L5 |
| **L7 Analytics Engines** | Scoring, valuation, risk, backtest, … | Engine interfaces + traced results (doc 08) | L6 |
| **L8 AI Layer** | Retrieval-grounded research assistance | AI service interfaces (doc 09) | L7 |
| **L9 API** | The one external contract | Versioned REST (doc 10) | L7, L8 |
| **L10 Frontend** | Terminal UI | — | L9 only |

**Enforcement:** the layer boundary is enforced by (a) module/package structure, (b)
dependency-direction linting in CI, and (c) code review mapping each module to its owning doc
(doc 02 §5, doc 11). A pull request that imports "upward" fails CI.

### Runtime decomposition (logical, not a deployment diagram — that's doc 12)
The stack is not one process. It is three cooperating planes:

- **Ingestion plane.** L1→L5. Batch/scheduled first; owns freshness. This is where the
  current `generate_snapshots.py` pipeline evolves into a real ingestion service.
- **Analytics plane (compute).** L6→L8. Runs on demand (API-triggered) and pre-computed
  (scheduled materialization). Pure functions over the domain store; horizontally scalable
  because it holds no authoritative state.
- **Serving plane (online).** L9→L10. Low-latency, read-mostly, stateless services reading
  from the domain store and a serving cache; never computes heavy analytics inline.

**Orchestration (v2.0, per review B3):** the ingestion and analytics planes do not schedule
themselves. All pipeline work — fetch, validate, normalize, persist, feature/analytics
materialization, invalidation cascades — runs as **declared DAGs under one orchestrator**,
with idempotent tasks, retries, and first-class backfill. The orchestration and
freshness-propagation model is owned by [doc 16](16-data-orchestration-and-freshness.md).

### Boundary & style decisions
- **Modular monolith with module-owned schemas (v2.0, per review B7).** Start as a
  well-partitioned modular monolith whose module seams are the layer boundaries above.
  Crucially: **each module owns its schema, and no module reads another module's tables.**
  Cross-module access goes through the owning module's published interface (repositories,
  feature/engine contracts) — the database is a *system of record*, never a cross-module
  integration bus. This resolves the v1.0 contradiction between "shared DB as integration
  point" and "service-extractable": extraction is real only if data ownership is already
  partitioned. A module is extracted into its own service *only* when scale or team
  boundaries demand it (principle 18).
- **Pipelines integrate through orchestration, not through the database.** Sequencing,
  retries, backfills, and invalidation cascades are the orchestrator's job (doc 16). An event
  backbone is introduced only when streaming ingestion or cross-service choreography requires
  it (doc 15 gates this).
- **Everything derived is recomputable — within declared bounds (v2.0, per review B1).**
  Because raw is immutable and analytics are deterministic (principle 11/14), derived layers
  can be rebuilt from L2 — *provided* the effective-dated reference data and policy versions
  used at compute time are retained (doc 05), and *within* raw-retention windows (doc 17).
  Recompute is a recovery path with a measured RTO (doc 12), not an unbounded promise. The
  lineage guarantee tiers of principle 6 state precisely what "recomputable" means per surface.
- **Time is an explicit axis.** The system is bitemporal (event time vs. knowledge time).
  Every read can ask "as of when did we know this?" This decision shapes docs 04, 07, 08.

### Reference data-flow (one ticker, one metric)
```
provider.fetch(prices)               L1 adapter
  → raw_record{payload, fetched_at}  L2 immutable
  → validate(schema,ranges)          L3 → accept | quarantine
  → normalize → PriceObservation     L4 canonical (doc 04)
  → repo.save(bitemporal)            L5 domain store
  → feature: weekly_returns          L6 versioned feature
  → engine: sharpe_ratio(v2)         L7 → Result{value, inputs[], formula_version, lineage}
  → api: GET /securities/{id}/metrics L9 versioned response
  → terminal renders + "why?" panel  L10 shows lineage from the Result
```

## What must NOT live here
- Concrete schemas/tables (doc 07), endpoint shapes (doc 10), engine formulas (doc 08).
- Provider-specific details (doc 06) or the entity vocabulary (doc 04).
- Deployment topology, environments, scaling numbers (doc 12).

## Dependencies
- [01 Vision](01-vision.md), [02 Engineering Principles](02-engineering-principles.md).
- Directly constrains and is elaborated by docs 04–12.

## Completion criteria
- [ ] Every layer has exactly one owning downstream document for its contract.
- [ ] The dependency-direction rule is expressible as a CI check (import linting).
- [ ] The three planes (ingestion/analytics/serving) each have a clear state ownership story,
      and all pipeline work runs under the doc 16 orchestrator.
- [ ] Module-owned schemas: no cross-module table access exists (CI-checkable).
- [ ] The "recompute from L2" property is confirmed feasible by docs 05/07 *within* the
      lifecycle bounds of doc 17, with a measured RTO (doc 12).
- [ ] No component in the diagram lacks a home in a later document.
