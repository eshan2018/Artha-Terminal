# Architecture Review — v1.0 → v1.1 → Final v2.0 Audit

---

# PART II · Final Audit of Architecture v2.0 (2026-07-17)

| | |
|---|---|
| **Auditor role** | Principal Engineer (final adversarial pass; attempt to reject) |
| **Subject** | `docs/architecture/` v2.0 (docs 01–17 + README) |
| **Bar** | Only issues that would realistically block production. No stylistic findings. |
| **Verdict** | ✅ **No blocking issues found. Architecture v2.0 is approved for implementation**, with five non-blocking conditions to fold in during Phase 0 (below). |

## Audit method
Re-read the full set hunting for: unresolved contradictions, silent-corruption vectors,
compliance exposure, unproven guarantees, and anything the v1.0 review pattern would repeat.
The v1.0 blockers (B1–B12) were each re-verified as genuinely closed, not renamed.

## Findings — none blocking, five conditions

### C1 · `knowledge_time` must be *populated* from day one, not merely reserved
- **Severity:** High (silent-corruption class) · **Blocks implementation: NO** (one-sentence
  doc clarification; no design change)
- **Why it matters:** Docs 04/07 defer full price bitemporality to Phase 6 and "reserve the
  `knowledge_time` column so the upgrade is additive." Ambiguity: if the column is reserved
  but *unpopulated* until Phase 6, all pre-Phase-6 price history has no honest knowledge
  timestamps — Phase 6 backtests over that history would run on retroactively fabricated
  as-of data, which is exactly the lookahead dishonesty the architecture exists to prevent,
  and it would be undetectable.
- **Fix:** Stipulate in docs 04/07: *the `knowledge_time` value is written on every price/FX/
  reference ingestion from the first Phase 0.5 row; only the as-of query machinery is
  deferred to Phase 6.* Ingestion timestamps are free to capture and impossible to backfill.

### C2 · The strangler keeps a live public product on eval-grade feeds until Phase 8
- **Severity:** Medium-High (compliance exposure) · **Blocks implementation: NO** (it is the
  status quo of the already-live prototype; requires written acknowledgment, not redesign)
- **Why it matters:** v2.0's strangler pattern (correctly) keeps the public site live through
  Phases 0.5–7 — serving real users data derived from yfinance/free-tier feeds whose terms
  are personal/eval-grade. Doc 14 gates *commercial launch* on licensed feeds but does not
  explicitly accept the interim exposure of a *public, free* product on those feeds.
  Undocumented known risks are how compliance findings become compliance incidents.
- **Fix:** Add one dated risk-acceptance entry to doc 14's counsel-gate list: interim
  public-free operation on eval-grade feeds is a named, owned, accepted risk with a review
  date; monetization of any kind advances the licensed-feed gate from Phase 8 to that moment.

### C3 · Decimal↔float conversion boundary is undeclared
- **Severity:** Medium (correctness-at-the-seam) · **Blocks implementation: NO**
- **Why it matters:** Doc 04 mandates decimal money and float statistics — but prices
  (money, decimal) are the *input* to returns/volatility (statistics, float). Without a
  declared one-way conversion point, every feature author picks their own seam and parity
  tests (doc 11) chase phantom tolerance failures.
- **Fix:** One line in docs 04/08: money is decimal at rest, in the domain, and at the API;
  a single deterministic decimal→float conversion is permitted at feature-layer ingress for
  statistical computation; float→decimal reverse conversion is forbidden.

### C4 · Caches must be entitlement-aware or entitlements leak
- **Severity:** Medium (data-rights leak vector) · **Blocks implementation: NO**
- **Why it matters:** Doc 17 enforces entitlements at exactly two points (API edge, AI
  layer) — good. But the serving cache (doc 07) and any cached/pre-computed AI narratives
  (doc 09) sit *behind* those points: a projection cached for a higher-entitled requester and
  served to a lower one bypasses the engine without any code "violating" the design.
- **Fix:** One line in docs 10/17: cached/materialized serving and AI artifacts are keyed by
  entitlement context (or computed at the lowest tier and upgraded per-request); a cache hit
  must never widen entitlements.

### C5 · Invalidation cascades need stampede control
- **Severity:** Medium (operational blast radius) · **Blocks implementation: NO**
- **Why it matters:** Doc 16's protocol is correct but unbounded: one FX correction or an
  index-wide corporate action transitively invalidates enormous artifact sets; with `eager`
  policies this is a self-inflicted recompute storm on a 2-store, small-team platform.
- **Fix:** Add to doc 16's completion criteria: cascades are coalesced/batched with a
  declared concurrency budget, and `eager` is reserved for a small enumerated set of
  serving-critical artifacts.

## Explicitly examined and passed (no finding)
Single-Postgres blast radius (module schemas + per-scope crypto suffice at declared scale);
managed-orchestrator lock-in (portability documented, acceptable); walking-skeleton API
exception (scoped, disposable, justified); recompute-RTO evidence (measured, re-measured,
bounded — honest); bit-reproducibility feasibility (immutably materialized results make
"what did we show" answerable without archaeological re-execution); AI residual-risk framing
(honest, labeled, evaluable); DPDP/GDPR lifecycle coherence (policy 17 / keys 13 / tombstones
07 / evidence 05 — chain is closed); roadmap gate alignment (every deferral has one owner and
one opening phase).

## Verdict

The v1.0 failure modes — overclaimed guarantees, self-contradiction, missing keystones,
machinery beyond team capacity — do not recur in v2.0. The five conditions above are
one-line doc amendments at Phase 0, none altering any owned decision.

**Architecture v2.0 is approved for implementation.**

---

# PART I · Historical record: the v1.0 review that produced v2.0

| | |
|---|---|
| **Reviewer role** | Principal Engineer (adversarial review, Bloomberg/Stripe/Palantir lens) |
| **Subject** | `docs/architecture/` v1.0 (docs 01–15) |
| **Date** | 2026-07-17 |
| **Verdict** | ❌ **BLOCK.** Do not approve v1.0 for production. Approve **v1.1** after the 10 blocking conditions below are resolved. |
| **Resolution** | ✅ **All blocking conditions (B1–B12) resolved in Architecture v2.0** (2026-07-17): docs 01–15 amended, docs 16–17 added. This file is retained as the historical review record; the live decisions are in the numbered documents. |

> This review deliberately does **not** defend the design. Every finding is written to reject
> it. Severity tags: **BLOCKER** (must fix before approval), **MAJOR** (fix before the phase
> that depends on it), **MINOR** (track, don't gate).

---

## Verdict in one paragraph

v1.0 is a *coherent* architecture and a *dangerous* one — dangerous because its greatest
strengths (immutability, bitemporality-everywhere, lineage-per-value, 7-store polyglot
persistence, provider router, an 11-layer enforced monolith) are exactly the machinery of a
30-engineer platform team, and this is not one. It **violates its own Principle 18** (build the
minimum; premature generalization is debt) more often than any other principle it defends. It
also ships two **latent correctness/compliance defects** that would not survive a real
production review: it conflates "traceable to raw" with "reproducible as shown," and it mandates
append-only immutability while simultaneously promising license-bound retention and user
deletion — a direct contradiction. And it delivers **zero user value until Phase 4**, which is a
business risk masquerading as engineering discipline. Fix the ten blockers; the bones are good.

---

## The 10 blocking conditions (the gate)

1. **Reproducibility is overclaimed.** "Recompute everything from Raw Store" ≠ "reproduce what
   we showed a user on date X." Normalization/analytics also depend on *reference data and
   policy* that change over time (symbology, corporate actions, FX, source-priority). Replaying
   raw through today's code + today's reference data yields *different* canonical values.
   → **Require:** version/snapshot reference data + policies, and define lineage in explicit
   tiers (traceable / recomputable / bit-reproducible) with a stated guarantee per data class.

2. **Immutability vs. erasure/retention is contradictory.** Doc 05 mandates append-only
   immutable raw "forever"; doc 14 promises license-mandated retention limits and (implicitly)
   user deletion. India's **DPDP Act 2023** and GDPR give users erasure rights. Append-only
   fights both. → **Require:** a data-lifecycle model — crypto-shredding/tombstoning for raw,
   segregated user-data lifecycle, enforced retention windows. Name DPDP explicitly.

3. **No orchestration abstraction exists.** The entire pipeline (fetch→validate→normalize→
   persist→features→analytics→serving) is described as "scheduled jobs" with no DAG,
   dependency, backfill, or reprocessing model. This is the keystone that's missing — the
   platform literally cannot run reliably without it. → **Require:** a Data Orchestration doc
   (new doc 16).

4. **No cache-invalidation / freshness-propagation model.** When a raw price or a corporate
   action lands (or is corrected), *which* materialized features, analytics, and serving-cache
   entries become stale? v1.0 has no answer. Materialized lineage without invalidation = silently
   wrong numbers. → **Require:** an invalidation/propagation design (in doc 16).

5. **Money as float is unstated and therefore assumed.** The prototype uses floats; v1.0 never
   forbids it. A Stripe reviewer rejects on sight. → **Require:** decimal for monetary values
   with defined precision/rounding; float permitted only for statistical quantities (returns,
   vol). Stated in principles + domain model.

6. **Over-provisioned persistence violates Principle 18.** Seven distinct stores + a provider
   router + multi-source reconciliation + blanket bitemporality, specified as *foundational*,
   before there is a second provider or a scale problem. → **Require:** collapse to **2 stores
   to start** (managed Postgres incl. time-series via partitioning; object storage for raw +
   deep history); scope bitemporality per data class; defer router/reconciliation to the phase
   that adds a 2nd source. Add TSDB/graph store only on *measured* need (gated).

7. **Shared-DB-as-integration contradicts service extraction.** Doc 03 says "integrate through
   the domain store" *and* "service-extractable by seam." A shared database is the classic
   anti-pattern that makes extraction hard. Pick one. → **Require:** commit to a modular
   monolith with **module-owned schemas and internal interface contracts** (no cross-module
   table reads), so extraction is real — or drop the extraction claim.

8. **The AI "no ungrounded claim can be surfaced" guarantee is unachievable.** Grounding/
   faithfulness checks are probabilistic; you cannot *guarantee* zero ungrounded output from an
   LLM. Worse, LLM-extracted `FundamentalFact`s that pass range validation are the exact
   "plausible wrong number" the platform fears. → **Require:** reframe to defense-in-depth +
   residual-risk register + mandatory AI-content labeling; a **candidate vs. authoritative**
   data tier where LLM-extracted facts are never merged into authoritative data without a
   second source or human confirmation.

9. **No entitlements abstraction.** Licensing enforcement (doc 14) is scattered as "flags" with
   no model tying *user tier × data-source license × field/delay*. This will sprawl into
   per-endpoint hacks. → **Require:** a unified entitlements model (new doc 17, with the
   lifecycle from blocker 2).

10. **Numeric testing leans on golden-master, which enshrines bugs.** A golden captured from
    first-write code becomes the spec even if wrong; hand-computed references don't scale to
    frontier/valuation. → **Require:** property-based tests + an independent reference
    implementation for each nontrivial engine; a documented procedure for validating the *first*
    golden; a numeric-tolerance policy.

**Nothing ships to production until 1–10 are resolved in v1.1.**

---

## Findings by category

### Hidden coupling
- **BLOCKER — Reproducibility coupling (see blocker 1).** Lineage silently couples every derived
  value to the *entire* reference-data + policy state at compute time, which v1.0 does not
  version. The "recompute from raw = DR + audit" claim is only true if reference data, FX,
  corporate actions, source-priority policy, *and* code are all pinned. As written, an audit
  replay would not reproduce the number the user saw.
- **MAJOR — The `AnalyticResult` envelope is co-owned by docs 04 and 08** ("04 reserves its
  shape, 08 defines internals"). Split ownership of a core type is how contracts drift. One doc
  owns it; the other references it.
- **MAJOR — Engine → repository escape hatch.** Doc 08 lets engines read canonical data "via
  repositories where needed," bypassing the feature layer. That "where needed" is precisely the
  "just this once" reach-around the blueprint claims to forbid. Either features are the only
  input, or the layer boundary is decorative.
- **MINOR — Bitemporality couples every query to as-of semantics** even where no consumer needs
  it, taxing every read path.

### Scaling bottlenecks
- **BLOCKER — Missing invalidation (blocker 4)** is also the primary scaling failure: without
  it you either recompute everything on every tick (cost explosion) or serve stale/ wrong
  derived values.
- **MAJOR — Lineage cardinality explosion.** A screen over 5,000 instruments × 50 metrics =
  250k results, each with input-reference + feature-version + lineage rows. Materialized broadly,
  lineage storage and write amplification can exceed the underlying data. No sampling/rollup/TTL
  strategy. Bitemporal-everything compounds this.
- **MAJOR — DB-as-integration point is the synchronization bottleneck.** Ingestion (bitemporal
  append + per-fact lineage writes) and analytics reads and serving reads converge on one logical
  store. The serving cache helps reads; it does nothing for the write path.
- **MAJOR — Heavy analytics in the request path.** The 2,000-sim Monte-Carlo frontier "on
  demand" is a synchronous CPU spike per call unless materialized — and materialization has no
  invalidation story (above).
- **MINOR — Ingestion throughput is gated on vendor rate limits** with no backpressure/priority
  model as universes widen.

### Overengineering (violations of Principle 18)
- **BLOCKER — Seven stores + router + reconciliation + blanket bitemporality as foundation
  (blocker 6).** This is FactSet-grade machinery specified before the constraints that justify
  it exist. It is the single biggest source of premature complexity.
- **MAJOR — Provider registry/router/failover/multi-source reconciliation** is designed in doc
  06 as if foundational, though the roadmap doesn't add a 2nd provider until Phase 5.
  Reconciliation is genuinely hard and should not be built until 2+ sources exist.
- **MAJOR — Meta-overengineering: a 15-doc, 11-layer, CI-enforced architecture for what is
  effectively a 1–3 person effort.** The governance ceremony may exceed delivery capacity. The
  architecture that is *correct* for the target platform can be *fatal* for the team that has to
  build it, because it front-loads foundation cost ahead of any user value.
- **MINOR — Streaming-ready stage contracts** add conceptual load for a 15-minute-freshness
  research product.

### Missing abstractions
- **BLOCKER — Orchestration/workflow (blocker 3)** and **cache invalidation (blocker 4)**.
- **BLOCKER — Entitlements (blocker 9).**
- **MAJOR — Corporate-action reprocessing.** When a split/dividend is announced or corrected,
  historical adjusted series and every dependent derived value must recompute. No trigger/
  propagation model (this is a special, high-stakes case of blocker 4).
- **MAJOR — Raw-payload schema-contract versioning.** Adapters map vendor→canonical, but when a
  vendor silently changes its payload shape, there's no raw-contract version/detection. This is
  how "no vendor name above L1" quietly breaks in practice.
- **MAJOR — First-class as-of query context** — bitemporality is mandated but not abstracted;
  as-of is sprinkled rather than a single temporal context object threaded through reads.
- **MINOR — Numerics/units** need a shared value type (money, ratio, points) rather than
  convention.

### Compliance blind spots
- **BLOCKER — Immutability vs. erasure/retention (blocker 2).**
- **MAJOR — India DPDP Act 2023 unnamed** despite the core user being the Indian retail
  investor; data-localization and consent obligations unaddressed.
- **MAJOR — Entitlement enforcement assumes a user-entitlement store that isn't modeled**
  (blocker 9). "Serve derived-only per source" is unenforceable without knowing each user's
  rights.
- **MINOR — Real-time attribution/delayed-data labeling** obligations from exchange licenses are
  generalized into "systematic disclosure" without the specifics licenses actually require.

### Data-lineage weaknesses
- **BLOCKER — Traceable ≠ reproducible (blocker 1).** The headline differentiator is
  under-specified in exactly the way that matters for audits and complaints.
- **MAJOR — Reconciliation decisions aren't in lineage.** "Chose source X over Y" depends on a
  policy that is itself versioned data; if it's not captured, lineage can't explain the choice.
- **MINOR — No lineage rollup/sampling** → cost (see scaling).

### Testing weaknesses
- **BLOCKER — Golden-master enshrines bugs; hand-computed refs don't scale (blocker 10).**
- **MAJOR — No numeric SLOs.** "Monitored like uptime" with no thresholds is not monitorable.
- **MAJOR — No load/performance or chaos/failure-injection tier.** "Graceful degradation" on
  provider outage is claimed but never tested.
- **MINOR — AI evals lack thresholds and a "who validates the validator" answer** for
  faithfulness checks.

### AI architecture risks
- **BLOCKER — Unachievable grounding guarantee + unvetted LLM-extracted facts (blocker 8).**
- **MAJOR — RAG corpus scope is hand-waved.** "Filings/news as first-class documents with
  lineage" is a multi-quarter ingestion/parsing/entity-linking programme hidden in a bullet.
- **MAJOR — Open-ended AI cost/latency is unbounded** and un-precomputable; no budget/circuit
  model beyond a mention.
- **MAJOR — Model-swap ≠ behavior-preserving.** "Swappable model vendor" is easy; swapping
  without output regression requires a strong eval gate that v1.0 only gestures at.
- **MINOR — Prompt-injection from retrieved content** is named but the defense is thin for a
  system whose corpus is untrusted filings/news.

### Future migration risks
- **BLOCKER — Shared-DB vs. service-extraction contradiction (blocker 7).**
- **MAJOR — Bitemporal schema migrations on decades of time-series** are brutal; "forward-only
  migrations" understates the cost of blanket bitemporality (another reason to scope it).
- **MAJOR — Vercel/serverless frontend won't host a stateful, DB-connected, compute-heavy API.**
  Phase 4 implicitly forces a hosting migration that v1.0 doesn't acknowledge.
- **MINOR — Repository-interface portability is partly illusory** — SQL vs. TSDB vs. graph have
  divergent query power; the interface leaks or degrades to lowest-common-denominator.

### Operational complexity
- **BLOCKER-adjacent — Ops surface exceeds plausible team capacity.** 7 stores × 3 planes ×
  orchestration × 3 telemetry classes × AI infra × secret rotation × IaC × progressive delivery.
  Who is on-call for the "freshness pages someone" alert? → folded into blockers 6 and the
  staffing/managed-first requirement below.
- **MAJOR — Recompute-from-raw as an RTO** is unquantified; at real scale it may be a
  multi-hour/day rebuild, which is not a recovery strategy until proven.
- **MINOR — Managed-vs-self-hosted is left open** on the critical path, maximizing early ops load.

### Business / delivery risk (not requested, but blocking in a real review)
- **MAJOR — Zero user value until Phase 4.** For a product still proving demand, a foundation-
  first plan with no earlier value is a strategic risk. The existing prototype must stay live and
  be strangled gradually, and a thin end-to-end slice must land early to de-risk the stack.

---

## What I require before approval (consolidated checklist)

- [x] **B1** Lineage reproducibility tiers defined; reference data + policy versioned/snapshotted.
- [x] **B2** Data-lifecycle model (erasure + retention) reconciled with immutability; DPDP/GDPR named.
- [x] **B3** Orchestration/workflow model (new doc 16).
- [x] **B4** Cache-invalidation & freshness-propagation model (doc 16), incl. corporate-action reprocessing.
- [x] **B5** Numeric standard: decimal money, precision/rounding, float scope.
- [x] **B6** Persistence right-sized to 2 stores; bitemporality scoped per data class; router/reconciliation deferred.
- [x] **B7** Modular-monolith commitment with module-owned schemas; drop DB-as-bus for cross-module integration.
- [x] **B8** AI reframed: defense-in-depth + candidate/authoritative tiers + labeling + residual-risk register.
- [x] **B9** Entitlements model (new doc 17).
- [x] **B10** Testing: property-based + reference-impl parity; numeric SLOs; load/chaos tier.
- [x] **B11** Managed-first, single-cloud posture + explicit staffing assumption; RTO/RPO quantified.
- [x] **B12** Walking-skeleton phase inserted; prototype kept live (strangler) — earlier time-to-value.

---

## Architecture v1.1 — proposal (the deltas from v1.0)

v1.1 keeps the layered invariant, the vision, the provider-abstraction principle, and the
analytics engine contract. It **changes the parts that overreached and fills the parts that were
missing.**

### D1 · Lineage & reproducibility, made precise *(amends 05, 07, 08)*
Define three guarantees and state which applies where:
- **Traceable** — every value links to its source records + formula version. (All values.)
- **Recomputable** — re-running current code reproduces current values. (All derived values.)
- **Bit-reproducible** — reproduce exactly what a user saw on date X, by pinning code +
  formula version + **an effective-dated snapshot of reference data & policy** (symbology,
  corporate actions, FX, source-priority). (Guaranteed for regulated/audited surfaces; offered
  best-effort elsewhere.) Reference data becomes effective-dated, versioned data — not ambient.

### D2 · Data lifecycle & governance → **new doc 17: Entitlements & Data Governance** *(amends 05, 13, 14)*
- Raw immutability reconciled with erasure via **crypto-shredding / tombstoning**; user PII is
  segregated with its own lifecycle and retention windows.
- **Entitlement engine:** `entitlement = f(user_tier, data_source_license, field, delay)`,
  enforced at the API edge and consulted by the AI layer. License terms (doc 06 metadata) +
  user tier resolve to what may be served, derived-only, or withheld.
- **DPDP Act 2023 + GDPR** named as first-class constraints; data-localization stance recorded.

### D3 · Orchestration & freshness → **new doc 16: Data Orchestration & Freshness** *(amends 03, 05, 12)*
- A **pipeline DAG** (managed scheduler/orchestrator; e.g. a Dagster/Temporal-class tool)
  owns fetch→validate→normalize→persist→materialize, with retries, backfill, and idempotency.
- A **derived-data dependency graph + invalidation protocol:** when an input (raw fact,
  corporate action, FX, policy) changes, the affected features/analytics/serving entries are
  marked stale and recomputed on a defined policy. Corporate-action reprocessing is a first-class
  workflow. This is the keystone v1.0 lacked.

### D4 · Right-sized persistence *(replaces doc 07's 7-store polyglot for the early phases)*
- **Start with two stores:** managed **PostgreSQL** (reference/master, fundamentals, economics,
  time-series via native partitioning/`TimescaleDB`-style, lineage as tables, derived results)
  + **object storage** (immutable raw capture, deep history, large blobs).
- **Scoped bitemporality** via a temporal-policy matrix: full bitemporal for fundamentals &
  economics (restatement-heavy); *effective-dated corrections* for prices initially, upgraded to
  full bitemporal **only when Phase-6 backtesting-as-of actually needs it.**
- **Gated escalation:** a dedicated TSDB, graph store for lineage, or a message/event backbone
  is introduced only when a written, measured constraint is hit — each an explicit roadmap gate.

### D5 · Integration model, decided *(amends 03)*
- Commit to a **modular monolith with module-owned schemas and internal interface contracts.**
  Cross-module access goes through interfaces, never another module's tables. The domain store is
  a system of record, **not** a cross-module message bus. This makes future service extraction
  genuinely possible instead of nominally possible.

### D6 · Numerics standard *(amends 02, 04)*
- **Decimal** for all monetary values with defined precision and rounding; **float** only for
  statistical/ratio quantities. A shared quantity type carries value + unit + currency. Banning
  float-money is a Principle-12 (correctness) requirement, not a style choice.

### D7 · AI, de-risked *(amends 09, 11)*
- Replace the zero-hallucination *guarantee* with **defense-in-depth + a residual-risk
  register + mandatory AI-content labeling + human-verifiable citations.**
- **Candidate vs. authoritative data tiers:** LLM-extracted facts land in a `candidate` tier and
  are **never** promoted to authoritative without a second source or human confirmation. The
  validation gate (doc 05) explicitly distrusts LLM extraction beyond range checks.
- **RAG corpus is phased:** start grounded on the platform's *own* analytics + methodology
  catalog; filings/news ingestion is its own scoped programme, not a bullet.
- **AI budget/circuit governance** and a **model-swap eval gate** (behavior regression thresholds)
  are mandatory, not aspirational.

### D8 · Testing rigor *(amends 11)*
- **Property-based tests + an independent reference implementation** for every nontrivial engine;
  golden-masters are seeded *only* from a validated reference, with a documented validation
  procedure and numeric-tolerance policy.
- **Numeric data-quality SLOs** (freshness, completeness, drift) with thresholds that page.
- A **load/performance tier** for serving and a **chaos/provider-outage** tier to actually prove
  graceful degradation.

### D9 · Operations, made survivable *(amends 12)*
- **Managed-first, single cloud** on the critical path (managed Postgres, managed orchestrator,
  managed object storage); portability escape hatches documented but not pre-built.
- **Explicit staffing assumption** recorded; the architecture's ceremony is scaled to it.
- **RTO/RPO quantified**, and recompute-from-raw timed on the walking skeleton before it's
  trusted as a recovery path.

### D10 · Roadmap rework *(replaces doc 15 sequencing at the front)*
- **Insert Phase 0.5 — Walking Skeleton:** the thinnest possible end-to-end slice — **5
  instruments, 1 provider, 1 metric, a minimal typed v1 endpoint, wired to the existing
  frontend** — exercising every layer (adapter→raw→validate→normalize→domain→feature→engine→API)
  in weeks. It de-risks the whole stack and validates recompute timing before broad investment.
- **Strangler, not big-bang:** the existing Streamlit/Next.js prototype **stays live as the
  product** and is strangled surface-by-surface as real endpoints replace snapshot JSON — so
  users are retained and value is continuous, not deferred to Phase 4.
- **Move heavy machinery to where it's used:** full bitemporality + backtesting-as-of arrive with
  Phase 6; the provider router/reconciliation arrives with the 2nd provider in Phase 5; the
  event backbone / extra stores are gated on measured need.

### Document-set changes summary
| Change | Docs affected |
|--------|---------------|
| Add **doc 16 — Data Orchestration & Freshness** | new |
| Add **doc 17 — Entitlements & Data Governance** | new |
| Lineage reproducibility tiers + effective-dated reference data | 05, 07, 08 |
| Right-sized persistence + scoped bitemporality + gated escalation | 07, 03 |
| Modular-monolith with module-owned schemas (drop DB-as-bus) | 03 |
| Numerics standard (decimal money) | 02, 04 |
| AI defense-in-depth + candidate/authoritative tiers + phased RAG | 09, 11, 14 |
| Property-based/reference-impl testing + SLOs + load/chaos | 11 |
| Managed-first + staffing + RTO/RPO | 12 |
| Walking-skeleton phase + strangler + deferred heavy machinery | 15 |

---

## Decision log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-17 | v1.0 **blocked**; 10 blocking conditions issued; v1.1 delta proposal authored. | Adversarial review: reproducibility, lifecycle, orchestration, invalidation, numerics, right-sizing, integration model, AI overclaim, entitlements, testing. |
