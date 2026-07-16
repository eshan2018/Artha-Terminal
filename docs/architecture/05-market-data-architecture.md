# 05 · Market Data Architecture

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B1 (reference pinning, lineage tiers), B2 (lifecycle), B3/B4 (defers execution to doc 16), B6 (reconciliation deferred), B8 (candidate tier) |
| **Owner** | Principal Data Architect |
| **Depends on** | [03 System Architecture](03-system-architecture.md), [04 Canonical Domain Model](04-canonical-domain-model.md), [16 Data Orchestration & Freshness](16-data-orchestration-and-freshness.md) |
| **Consumed by** | 06, 07, 08, 14, 16, 17 |

## Purpose
Define the ingestion pipeline that turns external vendor feeds into trustworthy canonical
data: capture → validate → normalize → persist, with lineage and quality guarantees at every
step. This is the "data is the foundation" principle made operational.

## Why it exists
The platform's entire credibility rests on the correctness and traceability of its data. This
document owns the *gates* that stand between messy vendor reality and the clean canonical
model everything else trusts.

## Decisions this document owns

### The ingestion pipeline stages (L1–L5 of doc 03)
1. **Fetch (adapter).** A Provider Adapter (doc 06) pulls data for a request (instrument(s),
   interval, range). It returns the vendor payload plus fetch metadata (provider, endpoint,
   request params, `fetched_at`, response status).
2. **Raw capture (immutable within lifecycle).** The verbatim payload is stored append-only
   in the **Raw Store** before any transformation. Nothing is discarded at capture; nothing is
   ever mutated in place. Raw data does, however, have a **declared retention class** and
   lawful-erasure mechanics (crypto-shredding) per doc 17 — "recompute from L2" (doc 03) holds
   *within retention windows*, and this is the root of every lineage chain.
3. **Validation (the gate).** Structural, semantic, and cross-source checks (below). Records
   pass, or are **quarantined** with a reason — never silently dropped, never silently fixed.
4. **Normalization — with pinned reference state (v2.0, per review B1).** Passing records are
   mapped into canonical entities (doc 04): units attached via typed Quantities, currency
   tagged, temporality applied per the temporal-policy matrix, corporate-action adjustments
   applied via first-class `CorporateAction` records (not vendor-magic adjusted columns taken
   on faith). Every normalization run **records the effective-dated versions of the reference
   data and policies it used** (symbology, calendars, corporate actions, FX, source priority)
   — this is what upgrades lineage from merely *traceable* to *recomputable/bit-reproducible*
   (principle 6 tiers). Reference state is an input, never ambient.
5. **Persist.** Canonical entities written to the Domain Store (doc 07) per their temporal
   class, each carrying a lineage handle back to its raw record(s), transformation version,
   and reference-data snapshot version.

**Execution:** all five stages run as idempotent tasks in orchestrated DAGs with declared
retries and first-class backfill — owned by [doc 16](16-data-orchestration-and-freshness.md).
This document owns *what* each stage does; doc 16 owns *how and when it runs*, including the
invalidation cascade when late or corrected data lands.

### Validation policy (owned here)
- **Schema validation** — shape/type/required-field conformance to the adapter's declared
  output contract.
- **Range & sanity checks** — non-negative volume, price > 0, returns within plausible bounds,
  index levels not FX-converted, timestamps within trading calendar for the venue.
- **Continuity checks** — gaps, duplicate bars, stale (unchanged) series, unexplained jumps
  that no `CorporateAction` accounts for.
- **Cross-source corroboration** — where multiple providers cover the same instrument,
  material disagreement raises a quality flag (see reconciliation below).
- **Fail-closed rule (principle 13).** A record that fails a hard check is quarantined and
  *does not* enter the canonical store; analytics see absence, never bad data. Soft checks
  attach a quality flag that travels with the data.

### Data quality & freshness
- **Quality dimensions tracked as data:** completeness, timeliness (freshness vs. SLA),
  validity, consistency (cross-source), and lineage-completeness. Each canonical fact carries
  a quality stamp; dashboards monitor these like uptime (doc 12).
- **Freshness SLAs are per data class**, not global: intraday prices, EOD prices,
  fundamentals (event-driven around filings), economics (release-calendar driven). The
  current 15-minute snapshot cadence is one SLA tier, not the architecture.
- **Multi-source reconciliation — deferred until a second source exists (v2.0, per review
  B6/principle 18).** The *policy slot* is designed now: a versioned, effective-dated
  **source-priority policy** per data class decides the authoritative value when providers
  disagree, and disagreements are recorded as lineage ("3 sources, 1 outlier, chose X because
  Y" — including the policy version that made the choice). The *mechanism* is built in the
  phase that adds the second provider (doc 15 Phase 5), not before.
- **Authority tiers at the gate (v2.0, per review B8).** The gate stamps every passing fact
  `authoritative` or `candidate` (doc 04). AI-extracted facts (doc 09) always enter as
  `candidate` regardless of validation outcome — range checks cannot vouch for an LLM's
  reading of a filing. Promotion to `authoritative` requires corroboration by a second
  independent source or explicit human confirmation.

### Ingestion modes
- **Batch/scheduled** (primary, day one): the evolution of `generate_snapshots.py` into a
  real ingestion service producing canonical data, not display JSON.
- **On-demand backfill**: historical range fetches for new instruments/universes, run through
  the same DAGs with correct `knowledge_time` semantics (doc 16).
- **Streaming**: explicitly **out of scope until a doc 15 gate opens it** (v2.0 tightening;
  principle 18). The stage contracts don't assume batch, which is sufficient future-proofing;
  no streaming-specific design work happens before the gate.

### Corporate actions & adjustment (called out because it's a classic silent-bug source)
- Adjustment factors are computed from stored `CorporateAction` records and applied
  transparently; both adjusted and unadjusted series are recoverable. The platform never
  trusts a vendor's opaque "adjusted close" as the sole truth.
- **Reprocessing (v2.0, per review B4):** a new, corrected, or late corporate action triggers
  the declared invalidation cascade — adjusted series and all downstream features/analytics
  recompute per policy, as one traceable reprocessing run. Mechanics owned by doc 16.

## What must NOT live here
- Vendor-specific fetch logic, auth, rate-limit handling, ret/quirk mapping — doc 06.
- Physical schema of raw/quarantine/canonical stores — doc 07.
- The formulas that *consume* this data — doc 08.
- Licensing/redistribution rules that constrain *what may be stored/served* — doc 14
  (this doc references those constraints; it does not decide them).

## Dependencies
- [04 Canonical Domain Model](04-canonical-domain-model.md) — the target shape of normalization.
- [06 Provider Abstraction Layer](06-provider-abstraction-layer.md) — supplies stage-1 fetches.
- [14 Compliance & Licensing](14-compliance-and-licensing.md) — constrains retention/redistribution.

## Completion criteria
- [ ] Every pipeline stage has a defined input/output contract and a failure mode, and runs as
      an idempotent task under the doc 16 orchestrator.
- [ ] Validation rule categories are enumerated with a pass/quarantine/flag disposition each,
      plus authority-tier stamping (authoritative/candidate).
- [ ] "Recompute canonical data from Raw Store" is demonstrated feasible *within doc 17
      retention windows*, with reference-data versions pinned per normalization run.
- [ ] Freshness SLA tiers and quality dimensions are named, monitorable, and thresholded.
- [ ] The source-priority policy slot is versioned data; the reconciliation mechanism is
      explicitly deferred to the second-provider phase.
- [ ] Corporate-action adjustment is auditable, reversible, and its reprocessing cascade is
      specified via doc 16.
