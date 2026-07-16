# 07 · Database Design

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B1 (lineage tiers), B2 (lifecycle bounds), B4 (invalidation participation), B6 (right-sized to two physical stores, scoped temporality), B7 (module-owned schemas); lineage-cardinality policy added |
| **Owner** | Principal Data Architect |
| **Depends on** | [04 Canonical Domain Model](04-canonical-domain-model.md), [05 Market Data Architecture](05-market-data-architecture.md) |
| **Consumed by** | 08, 10, 12, 13 |

## Purpose
Decide how canonical data, raw captures, lineage, and derived values are physically stored:
the storage engines, the logical schemas, the time-series strategy, and the lineage store —
such that traceability, immutability, and reproducibility (principles 6/11/14) are structural.

## Why it exists
The domain model (doc 04) is storage-agnostic on purpose. This document translates it into a
persistence design that can serve online reads fast, hold decades of time-series economically,
and prove lineage — three different access patterns that one naive schema cannot satisfy.

## Decisions this document owns

### Right-sized persistence: two physical stores, many logical roles (v2.0, per review B6)
v1.0 specified seven distinct stores as foundational — FactSet-grade machinery ahead of any
measured need, and the review's largest overengineering finding. v2.0 keeps the *logical
roles* (they name real access patterns) but maps them onto **two physical stores**, with a
written escalation path:

**Physical store 1 — managed PostgreSQL** (one instance, module-owned schemas per doc 03):
- *Reference / Master role* — instruments, companies, exchanges, symbology, universes,
  calendars, corporate actions; effective-dated + versioned (doc 04). Integrity-critical SQL.
- *Time-Series role* — price/economic/FX observations via **native partitioning** (or a
  Timescale-class extension) — partitioned, append-heavy, range-scan-optimized tables, not a
  separate TSDB.
- *Fundamentals role* — sparse, restatement-heavy line items; fully bitemporal.
- *Derived / Analytics role* — materialized `AnalyticResult`s + features with lineage handles;
  recomputable cache-with-provenance, participating in the doc 16 invalidation protocol.
- *Lineage role* — relational adjacency tables (the same structure doc 16 reads forward for
  invalidation).
- *Serving-cache role* — denormalized read projections; disposable, rebuildable. (An external
  cache tier is an escalation, not a default.)

**Physical store 2 — object storage**:
- *Raw Store role* — append-only verbatim vendor payloads + fetch metadata, encrypted under
  doc 17 crypto-shredding scopes; cheap, immutable-within-lifecycle, rarely read.
- *Deep-history / archive role* — cold partitions aged out of Postgres.

**Escalation gates (each requires a named, measured constraint + a decision record):**
| Escalation | Gate |
|---|---|
| Dedicated TSDB | Partitioned-Postgres range scans miss serving/compute SLOs at measured volumes |
| Graph store for lineage | Traversal depth/fan-out demonstrably exceeds relational adjacency performance |
| External serving cache (Redis-class) | Measured read latency/throughput exceeds Postgres projections |
| Event backbone | Streaming ingestion or cross-service choreography actually required (doc 15) |

**Portability rule:** application code talks to **repository interfaces** over the canonical
model (doc 04), never raw SQL/vendor client scattered through layers. Swapping or escalating
a storage engine is a repository-implementation change. **Module-owned schemas (doc 03, per
review B7):** no module queries another module's tables — cross-module reads go through the
owning module's interface, which is what keeps future service extraction real.

### Time & versioning strategy (the crux)
- **Temporality is scoped by the temporal-policy matrix (v2.0, per review B6; owned with
  doc 04):** fundamentals and economics are **fully bitemporal** (`event_time` +
  `knowledge_time`, as-of reads) from day one — restatements are their nature. Prices, FX,
  and reference data are **effective-dated with versioned corrections**, with the
  `knowledge_time` column **present and populated on every ingestion from the first Phase 0.5
  row (audit clarification C1)** — only the as-of *query machinery* is deferred to Phase 6, so
  the upgrade to full bitemporal reads is additive, not a migration of decades of
  time-series, and no historical bar is ever left without an honest knowledge timestamp.
- **Immutability within lifecycle:** no in-place updates to facts or published derived
  values. Corrections = new versions; supersession is recorded (doc 04). Retention classes
  and erasure mechanics (crypto-shredding for object storage, tombstoning for relational) are
  governed by doc 17 — lineage *structure* survives erasure; erased content resolves to an
  auditable tombstone.
- **Adjusted vs. unadjusted** price series both recoverable from stored corporate actions;
  corporate-action reprocessing cascades through the doc 16 invalidation protocol.

### Lineage as stored structure (not logs)
Every canonical fact and every `AnalyticResult` carries a foreign lineage handle. The lineage
tables answer, for any value the API emits: *which provider, which raw record(s), which
transformation/formula version, and which reference-data/policy snapshot produced this?* — in
bounded queries. The same tables, read forward, are doc 16's invalidation dependency graph.
This is the physical backing of the product's explainability differentiator (doc 01), at the
guarantee tier declared for that surface (principle 6).

**Lineage economics (v2.0, per the review's cardinality finding):** per-value lineage rows for
bulk materializations (e.g. a 5,000-instrument × 50-metric screen) would exceed the underlying
data in write volume. Lineage is therefore stored at **batch granularity for bulk runs** (one
lineage record per materialization run × formula version × reference snapshot — shared by all
values in the run) and at **value granularity for audited/served surfaces**. Both resolve to
the same chain; only the storage sharing differs. Retention/rollup of aged lineage follows
doc 17 retention classes.

### Operational data concerns
- **Partitioning/retention** per store and per data class (hot recent vs. cold deep history).
- **Quarantine store** for validation failures (doc 05), queryable for data-ops triage.
- **Migrations are versioned and forward-only**; schema changes are contract changes (doc 02
  §15) reviewed like API changes.
- **Backup/restore & recompute** are dual recovery paths: restore from backup *or* rebuild
  derived layers from the immutable Raw Store — the latter bounded by doc 17 retention windows
  and **timed on the walking skeleton (doc 15 Phase 0.5)** so its RTO is a measured number,
  not an assumption (v2.0, per review B11).

## What must NOT live here
- Which vendors fill these stores — docs 05/06.
- Formulas producing derived values — doc 08.
- API/DTO shapes — doc 10 (the API is a projection, not a table dump).
- Deployment/hosting of the databases (managed vs. self-hosted, sizing) — doc 12.
- Access-control implementation & encryption specifics — doc 13 (schema *supports* them;
  doc 13 *decides* them).

## Dependencies
- [04 Canonical Domain Model](04-canonical-domain-model.md) — what is stored.
- [05 Market Data Architecture](05-market-data-architecture.md) — how data arrives/immutability.

## Completion criteria
- [ ] Every logical role is mapped to one of the two physical stores; each escalation has a
      written, measurable gate.
- [ ] The temporal-policy matrix is implemented: full bitemporality where declared,
      effective-dated elsewhere, with the bitemporal upgrade reserved in-schema.
- [ ] Module-owned schemas: no cross-module table access (CI-checkable with doc 03).
- [ ] Lineage is answerable in bounded queries for any emitted value, at declared granularity
      (batch vs. value) and guarantee tier.
- [ ] Repository-interface boundary is defined so engines are swappable.
- [ ] "Rebuild derived data from Raw Store" is a validated recovery path with a measured RTO,
      bounded by doc 17 retention windows.
- [ ] Quarantine, retention (per doc 17 classes), and migration policies exist.
