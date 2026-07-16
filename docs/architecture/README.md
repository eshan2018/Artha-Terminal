# Nivesh Terminal — Engineering Blueprint

> **Version 2.0 — ✅ APPROVED BASELINE · FROZEN (2026-07-17).**
> v1.0 was **blocked** by an adversarial principal-engineer review
> ([REVIEW-v1.0-and-v1.1-proposal.md](REVIEW-v1.0-and-v1.1-proposal.md)); v2.0 resolved all
> twelve blocking conditions (B1–B12), passed the final audit, folded in audit clarifications
> C1–C5, and added docs 16–17. **All 19 documents are Approved; the architecture is frozen.**
> Implementation of the Walking Skeleton (Phase 0.5, doc 15) is authorized to begin.
> **From this point on, the architecture documents are authoritative, and any future
> architectural change requires a new ADR (doc 18) — not an in-place edit.** See
> [Governance](#governance) below.

This directory is the **single source of architectural truth** for Nivesh Terminal.
It is written *before* feature implementation so the foundation is designed once,
deliberately, rather than discovered accidentally through code.

Nivesh Terminal is a **production-grade financial intelligence platform for retail
investors** — a modular research terminal in the philosophical tradition of Bloomberg,
FactSet, Capital IQ, Koyfin and AlphaSense, scoped and priced for retail. It is *not* a
stock screener, *not* a chatbot, and *not* a scoring engine. Screening, scoring, chat and
valuation are **modules** that sit on a common data-and-analytics foundation.

## The load-bearing idea

Every decision in this blueprint serves one layered dependency rule. Data flows **down**
this stack; dependencies only ever point **up** it. Nothing skips a layer.

```
Market Data Providers
      ↓
Provider Adapters          ── replaceable, vendor-specific
      ↓
Raw Data                   ── captured verbatim, immutable
      ↓
Validation                 ── reject/quarantine bad data at the gate
      ↓
Normalization              ── vendor shapes → one shape
      ↓
Canonical Domain Model     ── the vocabulary of the whole platform
      ↓
Database                   ── system of record + lineage
      ↓
Feature Engineering        ── reusable inputs to analytics
      ↓
Analytics Engines          ── scoring, valuation, risk, backtest, …
      ↓
AI Layer                   ── consumes analytics, never raw providers
      ↓
REST API                   ── the only contract the frontend sees
      ↓
Frontend
```

## How to read this set

Read top to bottom. Each document is a **charter**: it owns a bounded set of decisions and
explicitly disclaims what belongs elsewhere. If two documents seem to both decide a thing,
that is a bug in the blueprint — file it, don't code around it.

| # | Document | Owns |
|---|----------|------|
| 01 | [Vision](01-vision.md) | What we are building and for whom; non-goals |
| 02 | [Engineering Principles](02-engineering-principles.md) | The rules every other doc must satisfy |
| 03 | [System Architecture](03-system-architecture.md) | Layers, boundaries, data flow, runtime shape |
| 04 | [Canonical Domain Model](04-canonical-domain-model.md) | The platform's shared vocabulary and entities |
| 05 | [Market Data Architecture](05-market-data-architecture.md) | Ingestion, validation, normalization, lineage |
| 06 | [Provider Abstraction Layer](06-provider-abstraction-layer.md) | The port/adapter contract for every vendor |
| 07 | [Database Design](07-database-design.md) | Storage engines, schemas, time-series, lineage store |
| 08 | [Analytics Framework](08-analytics-framework.md) | How every analytics engine is structured & traced |
| 09 | [AI Framework](09-ai-framework.md) | Grounding, retrieval, guardrails, no-advice boundary |
| 10 | [API Design](10-api-design.md) | The REST contract, versioning, auth surface |
| 11 | [Testing Strategy](11-testing-strategy.md) | What "correct" means and how it's proven |
| 12 | [Deployment Strategy](12-deployment-strategy.md) | Environments, pipelines, jobs, observability |
| 13 | [Security](13-security.md) | Identity, secrets, data protection, isolation |
| 14 | [Compliance & Market Data Licensing](14-compliance-and-licensing.md) | Redistribution rights, regulatory posture |
| 15 | [Development Roadmap](15-development-roadmap.md) | Build order that minimizes technical debt |
| 16 | [Data Orchestration & Freshness](16-data-orchestration-and-freshness.md) | Pipeline DAGs, backfill, invalidation & staleness propagation *(new in v2.0)* |
| 17 | [Entitlements & Data Governance](17-entitlements-and-data-governance.md) | User×license entitlements; retention & lawful erasure *(new in v2.0)* |
| 18 | [Architecture Decision Records](18-architecture-decision-records.md) | Permanent, immutable memory of *why* each decision was made (ADR-0001…0020) |
| 19 | [Architecture Readiness Checklist](19-architecture-readiness-checklist.md) | The go/no-go gate — verdict: **YES** (unconditional); both administrative gates closed |
| — | [Review v1.0 → v1.1 → v2.0 audit](REVIEW-v1.0-and-v1.1-proposal.md) | The adversarial reviews that produced and approved v2.0 (historical record) |

## Dependency graph between documents

```
01 Vision
  └─▶ 02 Principles
        └─▶ 03 System Architecture
              ├─▶ 04 Domain Model
              │     ├─▶ 05 Market Data ─▶ 06 Provider Abstraction
              │     │        │               ├─▶ 14 Compliance & Licensing
              │     │        │               └─▶ 17 Entitlements & Governance
              │     │        └─▶ 16 Orchestration & Freshness
              │     ├─▶ 07 Database ◀─ 16, 17
              │     │     └─▶ 08 Analytics ─▶ 09 AI ─▶ 10 API ◀─ 16 (staleness), 17 (entitlements)
              │     └────────────────────────────────────┘
              ├─▶ 11 Testing        (spans 03–10, 16, 17)
              ├─▶ 12 Deployment     (spans 03,07,10,16)
              └─▶ 13 Security        (cross-cutting; erasure keys for 17)
15 Roadmap sequences all of the above.
```

## Relationship to the current codebase

The repository today contains a **Streamlit feature prototype** mid-migration to
Next.js-on-Vercel (see [`MIGRATION.md`](../../MIGRATION.md)). That work proves product
demand and contains genuinely valuable assets, but it is **not** the target architecture.

| Existing asset | Role in the target architecture |
|----------------|---------------------------------|
| `shared/calculations.py` (pure pandas math) | **Seed** for the Analytics Framework (doc 08). Ported behind engine contracts, not lifted wholesale. |
| `tickers/*_universe.json` | **Seed** for the security master in the Domain Model (doc 04). |
| `shared/data_loader.py` (yfinance/NSE/Alpha Vantage) | **Reference** for the first Provider Adapters (doc 06); rewritten to the port contract. |
| `shared/ai_analysis.py` (Groq/Llama) | **Reference** for the AI Framework (doc 09); rebuilt with grounding + guardrails. |
| Next.js `web/` app | Becomes the Frontend that consumes the REST API (doc 10) instead of static JSON. |
| Scheduled-snapshot JSON pipeline | A **transitional** delivery mechanism; superseded by the API once the data platform exists. |

Nothing here requires throwing away working math. It requires putting that math *in its
correct place in the stack* and never letting a higher layer reach around it again.

## Governance

> **Baseline status: Architecture v2.0 is APPROVED and FROZEN (2026-07-17).** All 19 documents
> are `Approved`. Implementation may proceed against them.

1. **The set is approved as a whole.** v2.0 is the frozen baseline; the layered dependency rule
   (top of this file) is non-negotiable and changing it requires re-approving the set.
2. **Every document carries a Status.** All are `Approved`. Only `Approved` documents may be
   implemented against.
3. **Change is by ADR, not by silent edit (post-freeze rule).** Now that the baseline is frozen,
   any *material* change to an owned decision requires a **new ADR (doc 18)** that supersedes the
   prior one — the affected specification document is then updated to match, and a dated entry is
   added to its decision log. Accepted ADRs are immutable; the next ADR id is **ADR-0021**.
   (Non-material corrections — typos, clarifications that change no decision — may be made in place.)
4. **Code references the doc it satisfies.** Every module maps to exactly one owning document.
5. **Scope creep is a review failure, not a coding problem.** If an implementation needs a
   decision no document owns, the blueprint is incomplete — write an ADR and amend the owning
   document first.
6. **No redesign without an explicit request.** The architecture is authoritative; it is not
   reopened for revision except on a deliberate, stated decision to do so.

## Decision log (blueprint-level)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-17 | v1.0 blueprint authored; layered architecture adopted as the invariant. | Foundation-before-features mandate. |
| 2026-07-17 | v1.0 **blocked** by adversarial review; 12 blocking conditions issued. | See [REVIEW-v1.0-and-v1.1-proposal.md](REVIEW-v1.0-and-v1.1-proposal.md). |
| 2026-07-17 | **Doc 19 (Readiness Checklist) added** — go/no-go gate. Verdict: **YES to begin implementation**, conditional on two administrative sign-offs (G1 flip statuses to Approved; G2 fold in audit conditions C1–C5); zero architectural blockers; all legal dependencies correctly phase-gated to monetization, not the start. | Honest gate separating design-completeness from the pending human approval. |
| 2026-07-17 | **Doc 18 (ADRs) added** — permanent architectural memory; ADR-0001…0020 record the decisions approved in v2.0 (product philosophy, layering, modular monolith, canonical model, provider abstraction, internal IDs, normalization, PostgreSQL, object storage, deferred event bus, deferred microservices, REST-first, AI, analytics, scoring-as-module, decimal money, lineage, compliance, commercial data, walking skeleton). Next ID: ADR-0021. | Capture *why* separately from the living spec, immutably. |
| 2026-07-17 | **Final audit passed — v2.0 approved for implementation**, with five non-blocking Phase 0 conditions (C1–C5: populate `knowledge_time` from day one; document interim eval-feed risk acceptance; declare the decimal→float seam; entitlement-aware caching; invalidation stampede control). See PART II of [the review record](REVIEW-v1.0-and-v1.1-proposal.md). | No production-blocking issues found on adversarial re-read. |
| 2026-07-17 | **✅ Architecture v2.0 APPROVED & FROZEN.** User approved v2.0. Administrative actions completed: C1–C5 folded into docs 04/06/07/08/10/14/16/17; all 19 document statuses flipped `Draft for approval → Approved`; README/governance updated to the frozen baseline. Change control is now ADR-driven (next id ADR-0021). | Transition from design to implementation; the architecture is authoritative. |
| 2026-07-17 | **v2.0 issued**: all blockers resolved. Lineage guarantee tiers + versioned reference data (B1); lifecycle/erasure model, DPDP/GDPR (B2, doc 17); orchestration + invalidation (B3/B4, doc 16); decimal-money numerics (B5); persistence right-sized to 2 stores with escalation gates, scoped temporality, router deferred (B6); module-owned schemas (B7); AI defense-in-depth + candidate/authoritative tiers (B8); entitlements engine (B9, doc 17); property-based + reference-impl testing, SLOs, load/chaos (B10); managed-first + staffing + RTO/RPO (B11); walking skeleton + strangler roadmap (B12). Layered invariant, vision, and principles preserved. | Review acceptance (Option A). |
