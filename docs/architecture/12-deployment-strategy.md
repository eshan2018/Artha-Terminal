# 12 · Deployment Strategy

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blocker B11 (managed-first, staffing assumption, quantified RTO/RPO) + orchestrator runtime (B3) + API hosting reality |
| **Owner** | FinTech CTO |
| **Depends on** | [03 System Architecture](03-system-architecture.md), [07 Database Design](07-database-design.md), [10 API Design](10-api-design.md), [16 Data Orchestration & Freshness](16-data-orchestration-and-freshness.md) |
| **Consumed by** | 13, 15, 16 |

## Purpose
Define how the platform is built, released, run, and observed across environments — the
mapping from the logical planes (doc 03) to running infrastructure, plus the pipelines and
telemetry that keep it reliable.

## Why it exists
The layered architecture must survive contact with real operations: scheduled ingestion,
online serving, heavy analytics, and AI all have different runtime profiles. This document
makes those operable and portable without smuggling infrastructure decisions into application
layers.

## Decisions this document owns

### Environments & promotion
- **Distinct environments** — local/dev, staging (production-like data-ops), production —
  with identical build artifacts promoted between them (build once, deploy many).
- **Config & secrets are environment-injected**, never in code or images (doc 13). Data-source
  credentials, model keys, DB connection strings are environment concerns.

### Operating stance: managed-first, one cloud, sized to the team (v2.0, per review B11)
- **Explicit staffing assumption:** this platform is operated by a **1–3 person team** for the
  foreseeable phases. Every topology decision below is sized to that reality; the v1.0 review
  found the ops surface exceeded plausible capacity, and this section is the correction.
- **Managed-first on the critical path:** managed PostgreSQL, managed object storage, a
  managed orchestrator (doc 16), managed secret store. Portability escape hatches (SQL,
  open formats, containers) are *documented*, not pre-built (principle 8 without principle 18
  violations).
- **One cloud provider** for the backend until a measured reason exists to diversify.

### Runtime topology (planes → infrastructure)
Maps doc 03's three planes:
- **Ingestion plane** — DAGs on the managed orchestrator (the evolution of the GitHub-Action
  snapshot cron), sized for burst fetches within provider rate limits, isolated so a slow
  vendor can't stall serving.
- **Analytics plane** — stateless compute for on-demand engine calls (async, doc 10) +
  scheduled materialization DAGs; horizontally scalable, holds no authoritative state.
- **Serving plane** — the API + frontend. **Hosting reality (v2.0, per review):** the
  Next.js frontend can stay on Vercel, but the **API is a stateful-connection, DB-backed,
  compute-adjacent service that runs on the backend cloud** (containers), not on serverless
  edge functions — Phase 4 (doc 15) explicitly includes standing this up. Low-latency,
  stateless, read-mostly, fronted by cache/CDN.
- **Data stores** (doc 07: managed Postgres + object storage) behind repository interfaces.

### Delivery & release
- **Containerized, IaC-defined, reproducible builds.** Infrastructure is code; environments
  are reproducible; no snowflake servers.
- **CI/CD gates** run doc 11's suites (financial-correctness, contract, lineage, layer-lint,
  AI evals) before promotion; a red gate blocks release. Migrations (doc 07) run as controlled,
  forward-only, reviewed steps.
- **Progressive delivery** — staging soak on real data-ops before production; safe rollouts
  (canary/blue-green as scale warrants — not before, principle 18).

### Observability (principle 16 made concrete)
- **Three telemetry classes:** (1) system (latency, errors, saturation); (2) **data-ops**
  (freshness per SLA tier, quarantine rates, cross-source drift, pipeline success — doc 05);
  (3) **cost/usage** (provider quota burn, AI token spend — docs 06/09).
- **Data freshness/quality is alerted like uptime.** A stale or degraded feed pages someone;
  users are shown honest freshness/quality state rather than silent staleness.
- **Traceability in ops too** — job runs, ingestion batches, and analytic materializations are
  logged with the same lineage discipline the data carries.

### Resilience & recovery
- **Quantified RTO/RPO (v2.0, per review B11):** recovery objectives are declared per store
  and data class — e.g. serving restored within hours; RPO for canonical data bounded by
  backup cadence + re-ingestion of the gap. **Recompute-from-raw is timed on the walking
  skeleton (doc 15 Phase 0.5) and re-measured as volume grows**; it is only a recovery path
  while its measured duration fits the declared RTO.
- **Two recovery paths** (doc 07): restore from backup, or rebuild derived layers from the
  immutable Raw Store (bounded by doc 17 retention). Both are exercised via chaos drills
  (doc 11), not assumed.
- **Graceful degradation** — provider outage ⇒ serve last-known-good with explicit staleness
  flags (doc 16), never fabricate; adapter failover arrives with the router in Phase 5
  (doc 06). Degradation behavior is chaos-tested (doc 11).

## What must NOT live here
- Application/business logic or schemas.
- Security *policy* (identity, encryption, isolation rules) — doc 13 (deployment *implements*
  the mechanisms doc 13 mandates).
- The build *order* of features — doc 15.

## Dependencies
- [03](03-system-architecture.md) (planes), [07](07-database-design.md) (stores/recovery),
  [10](10-api-design.md) (serving), [11](11-testing-strategy.md) (gates), [13](13-security.md).

## Completion criteria
- [ ] Each plane has a runtime home, scaling stance, and isolation story — including the
      API's backend-cloud home (not serverless edge) and the orchestrator runtime.
- [ ] The staffing assumption is written down and the ops surface demonstrably fits it.
- [ ] Build-once/promote, IaC, and CI/CD gates (incl. migrations) are defined.
- [ ] The three telemetry classes — including data-ops freshness/quality with paging
      thresholds (doc 11 SLOs) — are specified and alertable.
- [ ] RTO/RPO are quantified per store/data class; recompute-from-raw is timed, and both
      recovery paths are chaos-drilled.
- [ ] Infrastructure portability escape hatches are documented (no hard lock-in on critical path).
