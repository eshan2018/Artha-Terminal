# 02 · Engineering Principles

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B1 (lineage tiers), B2 (lifecycle), B5 (numerics) |
| **Owner** | Chief Software Architect |
| **Depends on** | [01 Vision](01-vision.md) |
| **Consumed by** | All engineering documents (03–15) |

## Purpose
State the invariant rules that *every* other document and *every* line of future code must
satisfy. These are the acceptance criteria for the whole system's design.

## Why it exists
Principles turn a thousand future micro-decisions into applications of a few agreed rules.
When two designs are both plausible, the one that better honors these principles wins — no
further debate required.

## Decisions this document owns
The canonical principles and their concrete, testable meaning.

### The layered dependency invariant (non-negotiable)
1. **Data is the foundation.** No analytic, AI, or UI value exists that is not ultimately
   backed by ingested, validated, stored data.
2. **Analytics consume normalized data** — never raw provider payloads.
3. **AI consumes analytics** — never raw providers, never the database directly.
4. **The frontend consumes the API** — never the database, never analytics internals.
5. **Nothing bypasses the architecture.** A layer may depend only on the layer directly
   beneath it (via that layer's published contract). "Just this once" reach-arounds are the
   defect this whole blueprint exists to prevent.

### The trust invariants
6. **Every derived value is traceable to its source — with an explicit guarantee tier.**
   Lineage is a first-class stored artifact, not a log line, and it comes in three declared
   tiers (v2.0, per review B1):
   - **Traceable** — every value links to its source records, reference-data versions, and
     formula version. *Applies to all values.*
   - **Recomputable** — re-running current code over retained inputs reproduces current
     values. *Applies to all derived values within retention windows (doc 17).*
   - **Bit-reproducible** — the platform can reproduce exactly what it showed on date X by
     pinning code, formula versions, and an effective-dated snapshot of reference data and
     policy. *Guaranteed for audited/compliance-relevant surfaces; best-effort elsewhere.*
   Which tier applies to which surface is declared, never implied (docs 05/07/08).
7. **Every provider is replaceable.** No domain, analytics, AI, or API code names a vendor.
   Vendor knowledge is quarantined inside adapters (doc 06).
8. **Vendor lock-in is minimized.** This applies to data vendors *and* infrastructure:
   prefer portable interfaces (SQL, object storage, containers, open formats) over
   proprietary services on the critical path; where a managed service is used, keep the
   escape hatch documented.
9. **Compliance and licensing are designed in from day one** (doc 14), not retrofitted. Data
   we are not licensed to store or redistribute must be architecturally *impossible* to leak.
10. **Scoring is one analytics module — not the core.** No layer may assume "the score" is
    the platform's central output. The domain model must not privilege it.

### The engineering-quality principles
11. **Determinism & reproducibility.** Given the same inputs and versions, analytics produce
    identical outputs. Time, randomness, and "latest data" are explicit inputs, never
    ambient. **Reference data and policies (symbology, corporate actions, FX, source
    priority, entitlement policy) are themselves versioned, effective-dated inputs** — not
    ambient state (v2.0, per review B1). This is what makes lineage meaningful and backtests
    honest.
12. **Correctness over cleverness in financial math.** Formulas are specified, versioned, and
    unit-tested against known references. A wrong number is worse than a missing one.
13. **Fail closed on data quality.** Bad or suspect data is quarantined at the validation gate
    (doc 05); it must never silently reach analytics. Absence is surfaced, not faked.
14. **Immutability within a governed lifecycle.** Raw observations and published derived
    values are append-only and versioned: corrections create new versions and never overwrite
    history. "Append-only" means *no in-place mutation* — it does **not** mean *no end of
    life*: retention windows and lawful erasure (crypto-shredding/tombstoning) are part of the
    design (v2.0, per review B2; mechanics in doc 17). (Temporal semantics are *scoped per
    data class* — see the temporal-policy matrix in docs 04/07.)
15. **Contracts are explicit and versioned.** Every layer boundary (adapter port, domain
    schema, analytics interface, API) is a named, versioned contract with its own tests.
16. **Observability is not optional.** Every job, ingestion, and analytic emits structured
    telemetry; data freshness and quality are monitored like uptime.
17. **Least privilege everywhere** (doc 13): code, jobs, and humans get the minimum access
    required.
18. **Build the minimum that satisfies the current phase — no less, no more.** Premature
    optimization and premature generalization are both technical debt (doc 15 enforces this).
    v2.0 note: the v1.0 review found this principle violated by its own blueprint (7-store
    persistence, provider router before a 2nd provider, blanket bitemporality); v2.0 adds
    **written escalation gates** — heavier machinery may be introduced only when a named,
    measured constraint is hit (docs 07/15).
19. **Numerics are deliberate.** Monetary values use **decimal arithmetic** with defined
    precision and rounding rules per currency; binary floating point is permitted only for
    statistical quantities (returns, volatilities, ratios, simulation outputs) where relative
    error is acceptable. No bare float ever represents money (v2.0, per review B5; value
    types in doc 04).

## What must NOT live here
- Specific technologies, schemas, or endpoints (docs 03/07/10).
- Exceptions or edge-case handling — principles are unconditional; if a case needs an
  exception, the principle or the design is wrong.

## Dependencies
- [01 Vision](01-vision.md) — principles exist to protect the vision.

## Completion criteria
- [ ] Each principle is stated so that a design review can return a binary pass/fail against it.
- [ ] The layered dependency invariant is accepted as enforceable in code review and CI
      (e.g. import/dependency linting), not merely aspirational.
- [ ] No two principles conflict; where tension exists (e.g. portability vs. speed), the
      tie-breaker is written down.
