# 16 · Data Orchestration & Freshness

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 |
| **Owner** | Principal Data Architect |
| **Depends on** | [03 System Architecture](03-system-architecture.md), [05 Market Data Architecture](05-market-data-architecture.md), [07 Database Design](07-database-design.md), [08 Analytics Framework](08-analytics-framework.md) |
| **Consumed by** | 05, 07, 08, 10, 12, 15 |

> Added in v2.0 to resolve review blockers **B3** (no orchestration abstraction) and **B4**
> (no cache-invalidation / freshness-propagation model). These were the two keystone gaps in
> v1.0: pipelines that cannot be reliably sequenced, and materialized values that cannot know
> they have gone stale.

## Purpose
Define (a) **how pipeline work is orchestrated** — the DAG of fetch → validate → normalize →
persist → feature → analytics → serving materialization, with retries, backfills, and
idempotency — and (b) **how freshness propagates**: when an input changes, exactly which
derived values become stale, and what happens next.

## Why it exists
v1.0 described the pipeline stages but not the machine that runs them. "Scheduled jobs" is not
an architecture: without dependency ordering, idempotent retries, and backfill semantics, the
ingestion plane cannot be operated; and without a derived-data dependency graph, materialized
lineage is just a confident audit trail attached to silently stale numbers. This document is
the platform's answer to the hardest question in derived-data systems: *how does a number know
it is out of date?*

## Decisions this document owns

### Orchestration model
- **All pipeline work runs as declared DAGs under one managed orchestrator** (a
  Dagster/Temporal-class managed tool per doc 12's managed-first rule; the specific product is
  a doc 12 selection, not an application-layer concern). No ad-hoc cron above the walking
  skeleton (doc 15 Phase 0.5).
- **Every task is idempotent and keyed.** A task is identified by (task type, canonical scope,
  time window, config version); re-running it converges to the same state (safe retries, safe
  replays). Non-idempotent side effects are forbidden in pipeline tasks.
- **Retries, timeouts, and dead-lettering are declared per task class**, mapped to the adapter
  error taxonomy (doc 06): `Transient` retries with backoff; `RateLimited` reschedules within
  quota; `Malformed`/`AuthFailed` alerts and dead-letters.
- **Backfill is a first-class operation**, not a special script: any DAG can be run for a
  historical window (new instrument, new universe, corrected history) with the same code path,
  writing with correct `knowledge_time` so backfilled data never masquerades as
  known-at-the-time data (preserves as-of integrity, docs 04/07).
- **Runs are lineage events.** Every DAG run records: code version, config/policy versions,
  reference-data snapshot version (doc 05), inputs consumed, outputs produced. Pipeline runs are
  part of the lineage chain (B1), not just ops logs.

### The derived-data dependency graph
- **Every materialized artifact declares its inputs.** Features, analytic results, and
  serving-cache projections each register the canonical facts, features, reference data, and
  policies they were computed from (this reuses the lineage handles of docs 07/08 — the
  dependency graph *is* lineage read in the forward direction).
- The graph is **queryable in both directions**: "what did this value use?" (lineage / audit)
  and "what uses this value?" (invalidation). One structure, two reads.

### The invalidation protocol
When an input changes — a new/corrected raw fact, a corporate action, an FX observation, a
reference-data or policy version, a formula version bump — the orchestrator:
1. **Marks** all downstream artifacts in the dependency graph **stale** (transitively).
2. **Schedules recomputation** per a declared per-artifact-class policy:
   - `eager` — recompute immediately (serving-critical projections);
   - `next-run` — fold into the next scheduled materialization (bulk features);
   - `on-read` — recompute lazily when next requested (rarely-read, parameterized results).
3. **Serves honestly in the interim**: a stale-but-not-yet-recomputed value is served *with its
   staleness flagged* in the `AnalyticResult` quality flags and at the API (doc 10). The
   platform never silently serves a value it knows is invalidated.

**Stampede control (audit clarification C5):** cascades are **bounded**, because one FX
correction or an index-wide corporate action can transitively invalidate very large artifact
sets. Recomputation is **coalesced and batched under a declared concurrency budget** (a
correction storm collapses to one recompute per affected artifact, not one per triggering
event), and the `eager` policy is **reserved for a small, enumerated set of serving-critical
artifacts** — everything else is `next-run` or `on-read`. This keeps invalidation from becoming
a self-inflicted recompute storm on the two-store, small-team platform (doc 12).

### Corporate-action reprocessing (the high-stakes special case)
A new, corrected, or late-announced corporate action invalidates the adjusted price series
from the action date forward — and therefore every feature/analytic derived from it. This is a
**declared, tested workflow**: ingest action → recompute adjustment factors → mark affected
series + downstream artifacts stale → recompute per policy → record the whole cascade as one
traceable reprocessing run. (Resolves the v1.0 MAJOR finding; doc 05 defers to this document
for the reprocessing mechanics.)

### Freshness as a contract
- **Per-data-class freshness SLOs** (doc 05 defines the tiers) are monitored by the
  orchestrator: expected-by times per DAG, with threshold-based paging (doc 12).
- **Freshness metadata travels to the edge**: every API response that includes canonical or
  derived data can state `as_of`, `computed_at`, and staleness status (doc 10). Honest
  staleness is a product feature (doc 01's trust differentiator), not an ops detail.

## What must NOT live here
- Validation rules and pipeline stage semantics — doc 05 (this doc *runs* the stages).
- Storage of the dependency graph / lineage — doc 07.
- Formula/feature definitions — doc 08.
- Orchestrator product selection and hosting — doc 12.
- Freshness *display* decisions — frontend concern behind the doc 10 contract.

## Dependencies
- [05](05-market-data-architecture.md) (stages + SLA tiers), [07](07-database-design.md)
  (lineage/dependency storage), [08](08-analytics-framework.md) (materialization policy),
  [10](10-api-design.md) (staleness surfacing), [12](12-deployment-strategy.md) (orchestrator
  runtime + paging).

## Completion criteria
- [ ] Every pipeline stage runs as an idempotent, keyed task in a declared DAG; no undeclared cron.
- [ ] Backfill uses the same code path and preserves `knowledge_time` correctness.
- [ ] The dependency graph answers "what uses this value?" in bounded queries.
- [ ] Each materialized artifact class has a declared invalidation policy (`eager` / `next-run` / `on-read`).
- [ ] Cascades are coalesced/batched under a declared concurrency budget; `eager` is limited to
      an enumerated serving-critical set (stampede control, C5).
- [ ] A corporate-action reprocessing cascade is specified end-to-end and testable (doc 11).
- [ ] Known-stale values are never served unflagged.
- [ ] DAG runs record code + config + reference-data versions as lineage events (supports B1).
