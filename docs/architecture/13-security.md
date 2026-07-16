# 13 · Security

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blocker B2: erasure key custody + DSR mechanics; entitlement enforcement linkage (doc 17) |
| **Owner** | FinTech CTO |
| **Depends on** | [03](03-system-architecture.md), [07](07-database-design.md), [10](10-api-design.md), [12](12-deployment-strategy.md) |
| **Consumed by** | 09, 10, 12, 14, 17 |

## Purpose
Define the security posture protecting the platform, its data, its users, and its credentials:
identity, authorization, secrets, data protection, isolation, and the AI-specific threats — as
a cross-cutting mandate every layer must satisfy.

## Why it exists
A financial platform is a high-value target and a custodian of user trust and vendor
relationships. Security designed in (principle 9/17) is cheap; retrofitted, it is a rewrite.
This document owns the rules; docs 10/12 implement them at their boundaries.

## Decisions this document owns

### Identity & access
- **Least privilege everywhere (principle 17)** — every human, service, and job gets the
  minimum access required. Ingestion can write raw; serving can only read canonical/serving
  stores; analytics can't call providers; etc. The layer boundaries (doc 03) are also *trust*
  boundaries.
- **Authentication & authorization enforced at the API edge** (doc 10). User identity,
  session/token management, and role/tenant scoping are defined here and applied there.
  (Credential entry/account creation is a *user* action the platform facilitates securely — it
  never handles raw passwords in application code.)
- **Service-to-service auth** between planes; no implicit trust from network position alone.

### Secrets & credentials
- **No secret in code, image, or repo.** Provider API keys, model keys, DB credentials are
  injected from a managed secret store per environment (doc 12); rotated; scoped. The
  prototype's `secrets.toml` pattern is replaced by managed secrets.
- **Vendor credentials are adapter-scoped** (doc 06) and never exposed above L1.

### Data protection
- **Encryption in transit and at rest** for canonical, derived, and especially any user data
  (portfolios, watchlists, workspaces).
- **Erasure-capable key management (v2.0, per review B2).** Doc 17's crypto-shredding depends
  on this document's mechanics: data in immutable stores is encrypted under **per-scope keys**
  (per-user for personal data; per-source-window for raw payloads) held in the managed key
  store; key destruction is the erasure primitive, is itself audited, and is irreversible by
  design. Key custody, rotation, and destruction procedures are owned here.
- **Data-subject requests (DPDP/GDPR) are bounded security operations** — access, correction,
  and erasure execute against the segregated user-data scope with full audit trail; doc 17
  owns the lifecycle policy, this document owns the mechanics.
- **PII minimization & separation** — user personal data is segregated (module-owned schema,
  per-user crypto scope) from market data, minimized, and access-audited. The platform stores
  as little about users as the features require.
- **Tenant/user isolation** — one user's portfolios/workspaces/AI history are never reachable
  by another; enforced in authorization *and* data access.
- **Audit logging** — security-relevant events (auth, access to user data, admin actions) are
  logged immutably, distinct from operational telemetry (doc 12).

### AI-specific security (with doc 09)
- **Prompt injection is a first-class threat.** Retrieved documents/filings/news are untrusted
  input; the AI layer must not execute instructions embedded in ingested content, must not be
  steerable into leaking system context or other users' data, and treats model output as
  untrusted until grounded/validated.
- **Data-egress control** — the AI layer cannot send platform data to model providers beyond
  what policy permits; prompts/context are governed and logged (doc 09).
- **No secret or cross-tenant data in prompts/context.**

### Application & supply-chain hygiene
- **Standard web hardening** at the API/frontend edge (authz on every endpoint, input
  validation, output encoding, rate limiting — doc 10).
- **Dependency & supply-chain security** — pinned, scanned dependencies; reproducible builds
  (doc 12); provenance for third-party code.
- **Defense in depth** — a single failure (leaked key, one bad input) should not cascade;
  isolation between planes contains blast radius.

## What must NOT live here
- Regulatory/licensing obligations (redistribution rights, advice rules) — doc 14 (security
  *enforces* some of them technically; doc 14 *decides* them).
- Deployment mechanics of secret stores / networks — doc 12 (this doc sets policy).
- Business logic of any layer.

## Dependencies
- [03](03-system-architecture.md) (trust boundaries = layer boundaries), [07](07-database-design.md)
  (data-at-rest, user data), [10](10-api-design.md) (edge enforcement), [12](12-deployment-strategy.md)
  (secret stores, network), [09](09-ai-framework.md) (AI threats).

## Completion criteria
- [ ] Least-privilege model maps to the layer/plane boundaries.
- [ ] Secrets are fully externalized, scoped, and rotatable; no secret in repo/image.
- [ ] Encryption in transit/at rest and user-data isolation are specified.
- [ ] Per-scope key management supports auditable, irreversible crypto-shredding (doc 17);
      DSR operations are bounded and audited.
- [ ] AI prompt-injection and data-egress threats have defined mitigations (with doc 09/11).
- [ ] Audit logging and supply-chain hygiene are defined.
