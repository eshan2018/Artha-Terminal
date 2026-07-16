# 10 · API Design

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review: entitlements enforcement via doc 17 (B9), staleness surfacing (B4), async heavy analytics |
| **Owner** | Chief Software Architect |
| **Depends on** | [04 Canonical Domain Model](04-canonical-domain-model.md), [08 Analytics Framework](08-analytics-framework.md), [09 AI Framework](09-ai-framework.md), [16 Data Orchestration & Freshness](16-data-orchestration-and-freshness.md), [17 Entitlements & Data Governance](17-entitlements-and-data-governance.md) |
| **Consumed by** | 11, 12, 13, Frontend |

## Purpose
Define the single contract through which the frontend (and any future client) consumes the
platform. The API is the *only* door to L9 (principle 4): no client touches the database,
analytics internals, or providers.

## Why it exists
The API is the platform's public shape and its stability contract. Designed well, the frontend
and backend evolve independently and the internal architecture stays free to change. Designed
badly, storage and vendor details leak to clients and every refactor becomes a breaking change.

## Decisions this document owns

### Core stance
- **REST/HTTP + JSON** as the baseline external contract (per the mandated target
  architecture), resource-oriented around the canonical domain (doc 04): securities,
  companies, prices, fundamentals, economics, universes, screens, portfolios, analytics,
  research/AI. Read-heavy; the domain nouns are stable, which suits REST.
- **The API is a *projection* of the domain, not a database dump.** DTOs are deliberately
  shaped for clients and decoupled from storage schemas (doc 07). Internal refactors must not
  force client changes.
- **Everything derived is served with its lineage available.** Metric/analytic responses
  expose (or link to) the `AnalyticResult` envelope — value, unit, formula version, as-of,
  and a lineage reference — so the frontend's "why?" panel is a first-class API capability,
  not an afterthought. This is the API expression of the product differentiator (doc 01).

### Contract discipline
- **Versioned from v1.** Explicit versioning (URI or header); breaking changes ⇒ new version,
  never silent mutation (principle 15). Deprecation policy is written.
- **Contract-first & typed.** A machine-readable schema (OpenAPI) is the source of truth,
  enabling generated clients/types for the Next.js frontend and contract tests (doc 11).
- **Consistent conventions** — pagination, filtering, sorting, sparse fieldsets, error shape
  (a common problem+reason model mirroring the analytics `Unavailable`/quality semantics),
  units/currency always explicit in payloads, and bitemporal `as_of` query support for
  point-in-time reads.
- **Idempotency & safety** — reads are cache-friendly and side-effect-free; any future
  mutating endpoints (watchlists, workspaces) are explicitly scoped and idempotent where
  possible.

### Boundaries & surfaces
- **Read/query API** (prices, fundamentals, analytics, screens) — the bulk, served from the
  serving plane + cache (doc 03/07), never computing heavy analytics inline. Responses carry
  **freshness metadata** (`as_of`, `computed_at`, staleness flags per doc 16): a known-stale
  value is served flagged, never silently (v2.0, per review B4).
- **Analytics API** — parameterized engine invocations returning traced results (doc 08).
  **Heavy computations are asynchronous** (submit → result handle → poll/fetch), never
  synchronous CPU spikes inside a request (v2.0).
- **AI/research API** — grounded, cited, labeled responses (doc 09); rate-limited, budgeted
  with circuit-breakers, async where long-running.
- **Auth surface** — authentication/authorization enforced at this boundary (mechanics in
  doc 13). Public/anonymous vs. authenticated capabilities are delineated here.
- **Entitlements enforcement (v2.0, per review B9):** the API edge is one of the exactly two
  enforcement points of the **doc 17 entitlements engine** — per-requester field filtering,
  delayed serving, derived-only projection, and attribution injection derive from versioned
  entitlement policy, not per-endpoint hacks. Rate limiting and quotas also live here.
  **Caches are entitlement-aware (audit clarification C4):** cached or materialized serving
  responses are keyed by entitlement context (or computed at the lowest tier and upgraded
  per-request), so a cache hit can never widen a requester's entitlements — enforcement points
  must not be bypassable by a projection cached for a higher-entitled requester.

### Transitional note
The current static-JSON snapshot delivery (`web/public/data/*.json`) is a **pre-API
stand-in**. It is superseded by this API once the data platform exists; the frontend migrates
from reading files to calling v1 (doc 15). The snapshot shape is *not* the API contract.

## What must NOT live here
- Business/analytics logic — the API is a thin, validated projection over docs 08/09.
- Storage schemas or vendor fields — docs 06/07 (must not leak into DTOs).
- Auth *implementation*, secret handling, encryption — doc 13 (this doc defines *where* auth
  applies; doc 13 defines *how*).
- Frontend rendering concerns.

## Dependencies
- [04](04-canonical-domain-model.md) (DTOs project the model), [08](08-analytics-framework.md)
  (traced results), [09](09-ai-framework.md) (AI responses).
- [13 Security](13-security.md), [14 Compliance & Licensing](14-compliance-and-licensing.md) — enforced at this edge.

## Completion criteria
- [ ] Resource model + versioning + error/units conventions are specified and contract-first (OpenAPI).
- [ ] DTOs are confirmed decoupled from storage schemas.
- [ ] Lineage/traceability is exposable for every derived value the API serves.
- [ ] `as_of` point-in-time querying is supported.
- [ ] Auth, rate-limit, and doc 17 entitlement enforcement (filter/delay/derived-only/
      attribution) are enforceable at the edge.
- [ ] Responses carry freshness/staleness metadata; heavy analytics are async.
- [ ] A migration path from static snapshots to v1 is defined.
