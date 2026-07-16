# 11 · Testing Strategy

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blocker B10 (property-based + reference implementations, golden governance, numeric SLOs, load/chaos tiers) + test classes for docs 16/17 |
| **Owner** | Chief Software Architect |
| **Depends on** | 03–10, 16, 17 |
| **Consumed by** | 12, 15 |

## Purpose
Define what "correct" means for a platform whose value is trustworthy numbers, and how that
correctness is *proven* continuously — with special attention to financial math, data
quality, layer-boundary integrity, and AI grounding.

## Why it exists
In finance, a plausible-looking wrong number is the worst possible defect: it is trusted and
acted on. Testing here is not a QA afterthought; it is how the platform earns the trust the
vision (doc 01) sells. It also mechanically enforces the layered invariant (doc 02).

## Decisions this document owns

### The test pyramid, financial-platform flavor
- **Unit — financial correctness (v2.0, hardened per review B10).** Three complementary
  mechanisms, because each alone fails:
  - **Reference-value tests** against hand-computed or authoritative examples — good for
    anchoring simple formulas, but they don't scale to frontier/valuation complexity.
  - **Property-based tests** asserting invariants over generated inputs (e.g. Sharpe is
    scale-invariant to currency; drawdown ∈ [-1, 0]; portfolio variance ≥ 0 for any valid
    covariance; adjusted series continuous across a split) — these catch the bugs no one
    thought to hand-compute.
  - **An independent reference implementation** for every nontrivial engine (different author
    or library), with parity asserted within a **documented numeric-tolerance policy**
    (per-quantity tolerances; decimal-money compares exactly, statistics within declared
    epsilon).
  Determinism is asserted: same inputs + versions ⇒ identical output; seeded Monte-Carlo
  reproduces exactly. Edge cases remain mandatory: missing data, single data point,
  splits/dividends, zero denominators (the prototype's `safe_div` discipline generalized).
- **Contract tests — layer boundaries.** Each Provider Adapter is tested against recorded
  vendor fixtures to prove it satisfies its port (doc 06). The API is tested against its
  OpenAPI contract (doc 10). Repository interfaces are tested against their canonical
  semantics (doc 07). These are the tests that make "swap a provider / storage engine"
  safe.
- **Data-quality tests — the validation gate.** The doc-05 validation rules have their own
  test suite (good data passes, each bad-data class quarantines, nothing silently mutates,
  authority tiers stamp correctly). Plus *ongoing* production data-quality monitors with
  **declared numeric SLOs and paging thresholds** (v2.0, per review: freshness per SLA tier,
  completeness %, cross-source drift bounds — "monitored like uptime" now has numbers).
- **Orchestration & invalidation tests (v2.0, new — doc 16).** DAG tasks are idempotent under
  replay; backfills preserve `knowledge_time`; an input change (fact correction, corporate
  action, policy version) marks exactly the declared downstream artifacts stale; a
  corporate-action reprocessing cascade recomputes end-to-end; no known-stale value is served
  unflagged.
- **Governance tests (v2.0, new — doc 17).** Entitlement decisions (filter/delay/derived-only/
  attribution) are asserted per tier × license fixture at the API edge and AI layer; erasure
  works — crypto-shredded raw is unrecoverable, tombstoned rows resolve as auditable absence,
  lineage structure survives; retention classes enforce.
- **Integration — pipeline & as-of.** End-to-end raw→validate→normalize→persist→feature→
  engine→API on fixture data. Explicit **lookahead-bias tests**: an as-of query at time T must
  never see data whose knowledge_time > T (backtest integrity, doc 08).
- **Lineage tests.** For a sampled derived value, assert the lineage chain resolves fully to
  raw records + formula version (the differentiator is *tested*, not assumed).
- **AI evaluation (doc 09).** Grounding/faithfulness evals (claims traceable to cited
  sources), no-advice-boundary red-team tests, prompt-injection resistance (doc 13), and
  regression eval sets — **with declared pass thresholds** feeding the residual-risk register,
  and serving as the **model-swap gate**: no model change ships without passing within
  regression bounds (v2.0).
- **Load/performance & chaos tiers (v2.0, new per review).** Serving-plane load tests against
  latency/throughput targets (also the evidence for doc 07 escalation gates); chaos/failure
  -injection for the claims v1.0 only asserted: provider outage ⇒ flagged last-known-good
  (never fabrication), orchestrator kill/retry ⇒ idempotent convergence, store failover ⇒
  recovery within measured RTO (doc 12).

### Enforcement mechanics
- **Dependency-direction linting** in CI enforces doc 03's layer rule and doc 06's "no vendor
  name above L1" — an upward import or a leaked vendor string fails the build.
- **Reproducibility in CI** — deterministic seeds, pinned versions, fixture-based data so runs
  are hermetic (no live-vendor dependence in unit/contract tiers).
- **Coverage is targeted, not vanity.** Non-negotiable coverage on financial math, validation,
  and lineage; pragmatic elsewhere (principle 18 — don't gold-plate glue code).
- **Golden-master / snapshot tests — with governed provenance (v2.0, per review B10).** A
  golden captured from first-write code enshrines its bugs as spec. Therefore: the *first*
  golden for any engine is seeded **only** after reference-implementation parity and
  property-test passes, via a documented validation procedure; thereafter goldens guard
  against unintended methodology drift, and changing one requires a `formula_version` bump +
  review.

## What must NOT live here
- The formulas themselves (doc 08) or endpoint shapes (doc 10) — testing *references* them.
- CI/CD pipeline plumbing and environments — doc 12 (this doc says *what* must be verified;
  doc 12 says *where/when* it runs).

## Dependencies
- All of 03–10 (defines what is under test). Feeds doc 12 (gates) and doc 15 (phase success).

## Completion criteria
- [ ] Each test tier has an owner concern and example cases, especially financial correctness.
- [ ] Every nontrivial engine has property-based tests + an independent reference
      implementation with a documented tolerance policy; goldens are seeded only from
      validated references.
- [ ] Layer-boundary + no-vendor-name + module-schema-ownership enforcement is defined as CI gates.
- [ ] Lookahead-bias, lineage-resolution, invalidation, entitlement, and erasure tests are
      explicit, mandatory test classes.
- [ ] Data-quality monitors have numeric SLOs with paging thresholds.
- [ ] AI grounding/no-advice/injection evals exist with pass thresholds and gate model swaps.
- [ ] Load and chaos tiers exist; degradation and recovery claims are demonstrated, not asserted.
- [ ] Determinism/reproducibility is a CI-enforced property.
