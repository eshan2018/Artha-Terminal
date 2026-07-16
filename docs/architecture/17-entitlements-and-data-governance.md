# 17 · Entitlements & Data Governance

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 |
| **Owner** | FinTech CTO / Principal Data Architect |
| **Depends on** | [04 Canonical Domain Model](04-canonical-domain-model.md), [06 Provider Abstraction Layer](06-provider-abstraction-layer.md), [14 Compliance & Market Data Licensing](14-compliance-and-licensing.md) |
| **Consumed by** | 05, 07, 09, 10, 13, 14 |

> Added in v2.0 to resolve review blockers **B2** (immutability vs. erasure/retention
> contradiction) and **B9** (no entitlements abstraction). v1.0 promised license enforcement
> via scattered "flags" and mandated append-only-forever storage while also promising
> retention limits and (by law) user erasure. This document reconciles both as one governance
> model.

## Purpose
Define (a) the **entitlements model** — the single abstraction deciding what any given
requester may see, at what granularity and delay, given data-source licenses and user tier —
and (b) the **data-lifecycle model** — how retention, expiry, and erasure coexist with the
platform's immutability and lineage guarantees.

## Why it exists
Without one entitlements abstraction, license enforcement sprawls into per-endpoint hacks and
eventually a redistribution breach. Without a lifecycle model, "append-only forever" collides
with the **India DPDP Act 2023** and **GDPR** erasure rights and with license-mandated
retention windows — a contradiction that only gets more expensive the longer data accumulates.

## Decisions this document owns

### The entitlements model (B9)
- **One function, one place:**
  `entitlement(requester_tier, data_source_license, data_class, field, market) →
  { serve | serve_delayed(Δ) | serve_derived_only | withhold }` (+ required attributions).
- **Inputs are data, not code:** adapter-declared license metadata (doc 06) and requester tier
  (anonymous / registered / paid / internal) resolve through versioned entitlement policy.
  Changing a license term or adding a tier is a policy-data change, not a code change.
- **Enforcement points are exactly two:** the **API edge** (doc 10 — field filtering, delay,
  derived-only projection, attribution injection) and the **AI layer** (doc 9 — retrieval and
  responses respect the caller's entitlements; the assistant can never surface data its user
  could not query directly). Nothing else needs license logic.
- **Caches sit behind, not around, the two enforcement points (audit clarification C4):** any
  cached or pre-computed artifact — serving-cache projections (doc 07) and pre-computed AI
  narratives (doc 09) — is keyed by entitlement context or computed at the lowest tier and
  upgraded per request. A cache hit must never widen entitlements; a materialized artifact is
  never served across an entitlement boundary it was not computed for.
- **Entitlement decisions are auditable:** denials/filters are logged (doc 13 audit class) and
  entitlement policy versions are part of the "what did we show on date X" reproducibility
  story (doc 05 lineage tiers).
- **Phasing:** at Phase 4 (single public tier) the model runs in its simplest configuration —
  one tier, per-source flags. The *abstraction* exists from the first API version so tiers and
  licensed feeds later (Phase 8) are configuration, not surgery (doc 15).

### The data-lifecycle model (B2)
Immutability (docs 02/05/07) is retained **within a governed lifecycle** — "append-only" means
*no in-place mutation*, not *no end of life*:
- **Retention classes** are declared per store × data class: e.g. raw vendor payloads (license-
  driven window), quarantine (ops window), canonical facts (long-lived), user data
  (account-lifetime + statutory), AI prompt/response logs (audit window). Every dataset has a
  declared class; "keep forever by default" is abolished.
- **Erasure mechanics that preserve integrity:**
  - **Crypto-shredding** for immutable/raw stores: data encrypted under per-scope keys
    (per-user for user data; per-source-window for raw payloads); destroying the key is the
    erasure. Key custody and destruction are doc 13 mechanics.
  - **Tombstoning** for relational stores: erased records are replaced by tombstones so
    referential and lineage *structure* survives while content is gone. A lineage chain that
    reaches erased content resolves to "erased under policy P on date D" — honest, auditable
    absence (consistent with principle 13).
- **User-data segregation:** personal data (portfolios, watchlists, workspaces, AI history)
  lives in its own module-owned schema (docs 03/07/13) with per-user crypto scope, making DSR
  (data-subject request) fulfillment — access, correction, erasure — a bounded operation, not
  an archaeology project.
- **Named regimes:** **DPDP Act 2023** (primary — Indian retail users; consent, purpose
  limitation, erasure, breach notification, and a data-localization stance to be confirmed with
  counsel per doc 14) and **GDPR** (applicable to any EU users). Doc 14 owns the counsel gates;
  this doc owns the technical model that can satisfy either answer.
- **Recompute-from-raw is bounded by lifecycle:** the doc 07 recovery path holds *within
  retention windows*; expired raw data is recoverable only as its canonical derivatives. Doc 07
  states this bound explicitly (no more unqualified "recompute everything forever").

## What must NOT live here
- License *terms* interpretation and counsel gates — doc 14 (this doc mechanizes its rulings).
- Encryption/key-management implementation — doc 13.
- API filtering mechanics — doc 10.
- Authorization for *platform* access (authN/Z) — doc 13; entitlements govern *data* rights,
  not identity.

## Dependencies
- [06](06-provider-abstraction-layer.md) (license metadata), [14](14-compliance-and-licensing.md)
  (rulings + counsel gates), [10](10-api-design.md)/[09](09-ai-framework.md) (enforcement
  points), [13](13-security.md) (keys, audit), [07](07-database-design.md) (retention classes,
  tombstones).

## Completion criteria
- [ ] The entitlement function's inputs/outputs are specified; policy is versioned data.
- [ ] Exactly two enforcement points (API edge, AI layer); no license logic elsewhere.
- [ ] Every store × data class has a declared retention class; none default to forever.
- [ ] Erasure is executable against immutable stores (crypto-shredding) and relational stores
      (tombstoning) without breaking lineage structure; tested (doc 11).
- [ ] DPDP/GDPR data-subject requests are bounded, auditable operations.
- [ ] The recompute-from-raw recovery bound is stated in doc 07.
