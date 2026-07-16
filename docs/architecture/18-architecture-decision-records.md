# 18 · Architecture Decision Records (ADRs)

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 |
| **Owner** | Chief Software Architect (custodian); each ADR names its deciding role |
| **Depends on** | 01–17 (records the decisions those documents specify) |
| **Consumed by** | Every engineer, every future architectural change |

## Purpose
This document is the **permanent architectural memory** of Nivesh Terminal. It records *why*
each major architectural decision was made — the context that forced it, the alternatives
weighed, the trade-offs accepted, and the conditions under which it should be revisited.

The numbered documents 01–17 are the **living specification** (the *what* and *how*, always
current). ADRs are the **immutable decision log** (the *why*, frozen at the moment of
decision). A specification tells a new engineer how the system works today; an ADR tells them
why it works that way and what it would cost to change — which is the knowledge that
otherwise evaporates when people leave.

## Scope
- **In scope:** decisions that are expensive to reverse, cross-cutting, or non-obvious —
  structural choices, technology commitments, deliberate deferrals, and the boundaries that
  define the platform's identity.
- **Out of scope:** implementation details, coding conventions, reversible local choices, and
  anything a single module owner can change without affecting another module. Those live in
  code and in the specification documents, not here.
- A useful test: *if reversing the decision later would require a migration, a re-architecture,
  or a renegotiation, it deserves an ADR.* If it would require only a pull request, it does not.

## ADR lifecycle
```
Proposed ──▶ Accepted ──▶ Deprecated
                 │
                 └──▶ Superseded by ADR-XXXX
```
- **Proposed** — drafted, under review; not yet binding.
- **Accepted** — approved and binding. The decision is now part of the architecture.
- **Deprecated** — no longer recommended, but not yet replaced (e.g. a deferral whose gate is
  about to open).
- **Superseded by ADR-XXXX** — replaced by a later decision. The record stays; only the status
  changes and a forward pointer is added.

An Accepted ADR is **never edited in substance and never deleted.** Reversing a decision means
writing a *new* ADR that supersedes the old one. History is append-only — the same principle
the data platform itself obeys (principle 14).

## ADR template
Every ADR uses exactly this structure:

```markdown
### ADR-XXXX · <Title>
- **Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYYY
- **Date:** YYYY-MM-DD
- **Deciding role:** <the architect role accountable for this decision>
- **Context:** The forces at play — the problem, constraints, and why a decision was required.
- **Decision:** What was decided, stated as a directive.
- **Alternatives:** The options seriously considered and not chosen.
- **Trade-offs:** What we give up by choosing this; the costs we knowingly accept.
- **Consequences:** What becomes true — positive and negative — once this is in effect.
- **Future revisit conditions:** The specific, observable triggers that should reopen this ADR.
- **Related documents:** The specification docs and other ADRs this decision binds to.
```

## Rules
1. **One decision per ADR.** If a record contains the word "and" between two independent
   choices, split it.
2. **ADRs are immutable once Accepted.** Change is expressed by supersession, never by editing
   the Context/Decision of an existing record.
3. **IDs are permanent and never reused.** A superseded ADR keeps its number forever.
4. **Every ADR names its revisit conditions.** A decision with no revisit trigger is dogma, not
   engineering. "Revisit never" is itself a valid, explicit trigger only for identity-defining
   product choices.
5. **The specification wins on "how"; the ADR wins on "why."** If a doc and an ADR disagree on
   *what the system does today*, the doc is current truth and a new ADR must be written to
   record the drift. They must never be silently inconsistent.
6. **Deferrals are decisions.** Choosing *not* to build something now, with a named gate, is an
   architectural decision and gets an ADR (see ADR-0010, ADR-0011).
7. **New ADRs are added, not retrofitted into history.** The next architectural decision is
   ADR-0021.

## Relationship to other architecture documents
- **README** holds the blueprint-level decision log (dated one-liners); this document holds the
  full reasoned records those lines summarize.
- **Docs 01–17** are the authoritative specification. Each ADR below points to the doc(s) that
  *own and elaborate* its decision. The ADR explains why the boundary exists; the doc defines
  where it runs.
- **REVIEW-v1.0-and-v1.1-proposal.md** is the adversarial history that pressure-tested these
  decisions (blockers B1–B12, audit conditions C1–C5). Several ADRs cite it as the evidence
  that the alternative was genuinely considered and rejected.

---

## ADR Index

| ID | Title | Status | Owning docs |
|----|-------|--------|-------------|
| [0001](#adr-0001--product-philosophy-a-research-terminal-not-a-screener-chatbot-or-score) | Product philosophy: a research terminal | Accepted | 01 |
| [0002](#adr-0002--strictly-layered-architecture-with-an-enforced-dependency-direction) | Strictly layered architecture | Accepted | 02, 03 |
| [0003](#adr-0003--modular-monolith-with-module-owned-schemas) | Modular monolith, module-owned schemas | Accepted | 03, 07 |
| [0004](#adr-0004--a-canonical-vendor-neutral-domain-model) | Canonical domain model | Accepted | 04 |
| [0005](#adr-0005--provider-abstraction-via-portsadapters) | Provider abstraction (ports/adapters) | Accepted | 06 |
| [0006](#adr-0006--platform-assigned-internal-identifiers) | Internal identifiers | Accepted | 04 |
| [0007](#adr-0007--normalize-at-a-validation-gate-with-pinned-reference-state) | Data normalization at a gate | Accepted | 05 |
| [0008](#adr-0008--postgresql-as-the-primary-system-of-record) | PostgreSQL as primary store | Accepted | 07 |
| [0009](#adr-0009--object-storage-for-immutable-raw-capture-and-deep-history) | Object storage for raw + archive | Accepted | 07 |
| [0010](#adr-0010--defer-the-event-bus) | Defer the event bus | Accepted (deferral) | 03, 16 |
| [0011](#adr-0011--defer-microservice-extraction) | Defer microservice extraction | Accepted (deferral) | 03 |
| [0012](#adr-0012--rest-first-api-as-the-single-client-contract) | REST-first API | Accepted | 10 |
| [0013](#adr-0013--ai-as-a-grounded-consumer-of-analytics-defense-in-depth) | AI architecture | Accepted | 09 |
| [0014](#adr-0014--analytics-as-uniform-versioned-traced-engines) | Analytics architecture | Accepted | 08 |
| [0015](#adr-0015--scoring-is-one-module-not-the-core) | Scoring as a module | Accepted | 01, 08 |
| [0016](#adr-0016--decimal-arithmetic-for-money) | Decimal money | Accepted | 02, 04 |
| [0017](#adr-0017--first-class-lineage-with-three-guarantee-tiers) | Lineage with guarantee tiers | Accepted | 02, 05, 07 |
| [0018](#adr-0018--compliance-and-lifecycle-designed-in-from-day-one) | Compliance & data lifecycle | Accepted | 13, 14, 17 |
| [0019](#adr-0019--commercial-data-strategy-eval-feeds-now-licensed-feeds-before-monetization) | Commercial data strategy | Accepted | 06, 14 |
| [0020](#adr-0020--walking-skeleton-first-strangle-the-prototype) | Walking Skeleton + strangler | Accepted | 15 |

---

### ADR-0001 · Product philosophy: a research terminal, not a screener, chatbot, or score
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** FinTech CTO
- **Context:** "Financial platform for retail investors" can collapse into any of several
  narrow products — a screener, an AI chatbot, a scoring engine — each of which would pull the
  architecture in an incompatible direction. Without a fixed identity, every technical decision
  is re-litigated against an imagined product.
- **Decision:** Nivesh Terminal is a **modular financial research and intelligence terminal**
  (Bloomberg/Koyfin philosophy, retail-appropriate) whose differentiator is **explainability +
  full lineage**. Screening, chat, and scoring are *modules*, never the core.
- **Alternatives:** (a) Ship a stock screener — fast to market, but a commodity with no moat.
  (b) Ship an AI research chatbot — trendy, but ungrounded and untrustworthy for finance.
  (c) Ship a scoring/ranking engine — simple, but reduces the platform to one opinionated number.
- **Trade-offs:** We accept a **slower, foundation-heavy path to value** in exchange for a
  defensible product. We forgo the quick win of a single-feature launch.
- **Consequences:** The layered, lineage-first architecture becomes mandatory rather than
  optional. Every feature must justify itself as a module on a shared foundation. Non-goals
  (no brokerage, no personalized advice, no HFT) are architectural constraints.
- **Future revisit conditions:** Revisit only on a deliberate, business-level pivot of what the
  product *is* — not for any feature request. This is an identity decision.
- **Related documents:** [01 Vision](01-vision.md); constrains all others.

### ADR-0002 · Strictly layered architecture with an enforced dependency direction
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** The product moat is traceability. Traceability is only real if data flows in one
  direction and no layer reaches around another (e.g. AI reading raw vendor data, or the
  frontend querying the database). "Discipline" alone does not hold this line under deadline
  pressure.
- **Decision:** Adopt an **11-layer stack** (Providers → Adapters → Raw → Validation →
  Normalization → Domain Model → DB → Features → Analytics → AI → API → Frontend). A layer may
  depend only on the published contract of the layer directly beneath it. The rule is
  **enforced in CI** by dependency-direction linting, not left to review.
- **Alternatives:** (a) Pragmatic/ad-hoc coupling — faster short-term, but destroys lineage.
  (b) Event-driven choreography from day one — flexible, but premature complexity (see ADR-0010).
- **Trade-offs:** More indirection and boilerplate at boundaries; a learning curve for
  contributors. We accept ceremony in exchange for a guarantee that lineage cannot be bypassed.
- **Consequences:** "Nothing bypasses the architecture" becomes a structural fact, CI-checkable.
  Any reach-around fails the build. Layer boundaries double as trust boundaries (doc 13).
- **Future revisit conditions:** If CI enforcement proves unworkable in practice, or if a layer
  is found to add no value, revisit the layer count — never the direction rule.
- **Related documents:** [02 Principles](02-engineering-principles.md), [03 System Architecture](03-system-architecture.md).

### ADR-0003 · Modular monolith with module-owned schemas
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** A 1–3 person team must ship a large platform. Microservices would impose
  distributed-systems overhead with no compensating benefit at this scale. But a naive monolith
  with a shared, cross-read database becomes impossible to later decompose (the v1.0 review
  flagged this contradiction, blocker B7).
- **Decision:** Build a **modular monolith** where **each module owns its schema and no module
  reads another module's tables** — cross-module access goes through published interfaces. The
  database is a system of record, never a cross-module integration bus.
- **Alternatives:** (a) Microservices now — rejected as premature (ADR-0011). (b) Shared-schema
  monolith — simplest, but bakes in coupling that makes future extraction a rewrite.
- **Trade-offs:** We give up the convenience of arbitrary cross-module joins and accept
  interface boilerplate between modules, in exchange for a genuine (not nominal) extraction path.
- **Consequences:** Future service extraction is a real option, gated by ADR-0011. A
  `no-cross-module-table-access` lint joins the CI gates (doc 15 Phase 0).
- **Future revisit conditions:** See ADR-0011 for extraction triggers.
- **Related documents:** [03 System Architecture](03-system-architecture.md), [07 Database Design](07-database-design.md).

### ADR-0004 · A canonical, vendor-neutral domain model
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** Multiple data vendors, each with its own shapes, quirks, and identifiers. If any
  vendor's shape leaks above normalization, every analytic and API is coupled to that vendor and
  provider-replaceability (a core principle) is dead.
- **Decision:** Define a **single canonical domain model** — the vendor-neutral vocabulary
  (Instrument, Company, PriceObservation, FundamentalFact, etc.) into which all vendor data is
  translated exactly once. Everything above normalization speaks only this language.
- **Alternatives:** (a) Pass vendor payloads upward and adapt per-consumer — minimal upfront
  work, maximal long-term coupling. (b) Adopt a vendor's model as canonical — free schema, but
  permanent lock-in to that vendor's worldview.
- **Trade-offs:** Upfront modeling cost and ongoing mapping effort; the model must be designed
  before much data flows. We accept this to keep everything above it stable and vendor-agnostic.
- **Consequences:** Provider swaps (ADR-0005) become adapter-level changes. The model is the
  contract spine of the platform; it carries typed Quantities (ADR-0016), authority tiers, and
  a scoped temporal policy.
- **Future revisit conditions:** Revisit specific entities as new data classes (options,
  fixed-income analytics) require them — additively. The *principle* of a canonical model does
  not revisit.
- **Related documents:** [04 Canonical Domain Model](04-canonical-domain-model.md).

### ADR-0005 · Provider abstraction via ports/adapters
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** Data vendors change terms, prices, quality, and availability. The prototype
  interleaved yfinance/NSE/Alpha Vantage quirks with business logic — the exact coupling that
  makes a vendor change a rewrite.
- **Decision:** Every vendor sits behind a **port (a platform-defined interface in canonical
  terms) implemented by an adapter**. All vendor knowledge — auth, quirks, field names, rate
  limits, license terms — lives *inside* the adapter and nowhere else. No vendor name appears
  above L1 (CI-enforced).
- **Alternatives:** (a) Direct SDK calls where needed — simplest, but couples the platform to
  each vendor. (b) A single "universal" data client — leaks the union of all vendors' quirks.
- **Trade-offs:** An abstraction layer to design and maintain; some vendor capabilities are
  flattened to the common contract. We accept this for replaceability and testability.
- **Consequences:** Adding/removing a provider is an adapter change with zero edits above L1.
  Adapters declare license metadata (feeds ADR-0018/0019) and a versioned raw-payload contract
  that detects vendor drift.
- **Future revisit conditions:** If a port's common contract is found to flatten away a
  capability the product genuinely needs, revisit that port's shape.
- **Related documents:** [06 Provider Abstraction Layer](06-provider-abstraction-layer.md).

### ADR-0006 · Platform-assigned internal identifiers
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** Vendor tickers collide and overload (`RELIANCE.NS` vs a US `RELIANCE`; `^NSEI`
  the index vs an equity; the same ISIN across venues). Using any vendor identifier as a primary
  key propagates that vendor's ambiguity into every table and query.
- **Decision:** The platform assigns its **own internal identifiers** (`InstrumentId`, etc.).
  No vendor identifier (ticker, ISIN, CUSIP, vendor symbol) is ever a primary key. Vendor IDs
  are cross-reference *attributes* resolved through a symbology table.
- **Alternatives:** (a) ISIN as primary key — standard, but not universal (indices, FX, some
  instruments lack one) and not vendor-neutral. (b) Vendor ticker as key — trivially breaks on
  collision and vendor swap.
- **Trade-offs:** A symbology-resolution layer to build and maintain; an extra indirection on
  every lookup. We accept this to make identity unambiguous and vendor-independent.
- **Consequences:** Ticker collisions resolve to distinct internal IDs (a Phase 1 success
  criterion). Symbology is the single place identity ambiguity is handled.
- **Future revisit conditions:** Revisit the ID scheme only if it fails to represent a required
  instrument class; never revert to vendor IDs as keys.
- **Related documents:** [04 Canonical Domain Model](04-canonical-domain-model.md).

### ADR-0007 · Normalize at a validation gate with pinned reference state
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** Vendor data is messy, occasionally wrong, and sometimes silently corrupt (the
  prototype's ~95× index FX-inflation bug is the archetype). Bad data that reaches analytics
  produces plausible wrong numbers — the worst defect class in finance.
- **Decision:** All data passes a **validation gate** (schema, range, continuity, cross-source)
  before normalization into the canonical model. Failures are **quarantined, never silently
  fixed or dropped** (fail-closed). Normalization **records the effective-dated versions of the
  reference data and policies it used**, so lineage is reproducible (ADR-0017).
- **Alternatives:** (a) Trust vendor data, validate lazily downstream — cheaper, but lets
  corruption reach users. (b) Normalize first, validate the canonical result — loses the raw
  context needed to diagnose failures.
- **Trade-offs:** Ingestion is slower and more complex; some good-but-unusual data may
  quarantine and need rule-tuning. We accept latency and false-positives to guarantee analytics
  never see bad data.
- **Consequences:** Analytics see absence, never fabrication (principle 13). Reference-state
  pinning is what upgrades lineage from *traceable* to *recomputable/bit-reproducible*.
- **Future revisit conditions:** Revisit specific validation rules continuously (they are data);
  the fail-closed gate itself does not revisit.
- **Related documents:** [05 Market Data Architecture](05-market-data-architecture.md).

### ADR-0008 · PostgreSQL as the primary system of record
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** v1.0 specified seven distinct stores as foundational — FactSet-grade polyglot
  persistence ahead of any measured need, and the review's largest overengineering finding
  (blocker B6). The workloads (relational reference data, time-series, fundamentals, derived
  results, lineage) are different, but not yet at a scale that forces different engines.
- **Decision:** Use **one managed PostgreSQL instance** as the primary system of record for
  reference/master, time-series (via native partitioning / a Timescale-class extension),
  fundamentals, derived results, and lineage — with **module-owned schemas** (ADR-0003).
  Additional engines (dedicated TSDB, graph store, external cache) are introduced only through
  **written escalation gates** tied to a measured constraint.
- **Alternatives:** (a) Polyglot from day one (v1.0) — matches access patterns, but multiplies
  ops surface for a tiny team. (b) A NoSQL/document store — flexible, but sacrifices the
  relational integrity and SQL portability the domain needs.
- **Trade-offs:** One engine serves several workloads sub-optimally; a single instance is a
  larger blast radius. We accept "good enough for current scale" plus a gated escalation path
  over premature specialization.
- **Consequences:** Drastically smaller ops surface, fitting the staffing reality (ADR-0020,
  doc 12). Repository interfaces keep engines swappable when a gate opens.
- **Future revisit conditions:** Partitioned-Postgres range scans miss serving/compute SLOs at
  measured volume → TSDB gate; lineage traversal outgrows relational adjacency → graph gate;
  read latency exceeds targets → external cache gate.
- **Related documents:** [07 Database Design](07-database-design.md).

### ADR-0009 · Object storage for immutable raw capture and deep history
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** Raw vendor payloads must be captured verbatim and immutably (the root of every
  lineage chain and the "recompute from raw" recovery path), but they are large, write-once, and
  rarely read — a poor fit for a hot relational store.
- **Decision:** Store **raw captures and aged-out deep history in object storage**, append-only,
  encrypted under per-scope keys (enabling crypto-shredding, ADR-0018). This is the second and
  only other physical store alongside PostgreSQL.
- **Alternatives:** (a) Keep raw in Postgres — simple, but bloats the hot store with cold data.
  (b) Discard raw after normalization — cheapest, but destroys lineage and recovery.
- **Trade-offs:** A second storage system to operate; raw reads are slower. We accept this for
  cheap, durable, immutable capture and a clean lifecycle boundary.
- **Consequences:** "Recompute canonical data from raw" is feasible within retention windows
  (ADR-0017/0018); recovery RTO is measured on the walking skeleton (ADR-0020).
- **Future revisit conditions:** If raw-read latency becomes a recompute bottleneck at scale,
  revisit the storage tier/format.
- **Related documents:** [07 Database Design](07-database-design.md).

### ADR-0010 · Defer the event bus
- **Status:** Accepted (deferral)
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** Event-driven architectures are powerful and fashionable, but an event backbone
  adds significant operational and reasoning complexity. At current scale, pipeline integration
  is handled by a DAG orchestrator (doc 16), and layers integrate through the domain store.
- **Decision:** **Do not build an event bus now.** Integrate pipelines through orchestration and
  the domain store. Introduce an event backbone only when streaming ingestion or genuine
  cross-service choreography requires it.
- **Alternatives:** (a) Event bus from day one — maximal flexibility, premature complexity for a
  batch-oriented, 15-minute-freshness research product. (b) Never — forecloses streaming, which
  the product may eventually want.
- **Trade-offs:** We give up event-driven flexibility and real-time reactivity now, in exchange
  for a far simpler operational model. Retrofitting a bus later has a cost we knowingly defer.
- **Consequences:** The system stays batch/scheduled and comprehensible. Stage contracts avoid
  assuming batch, so a streaming path can be added without redesign.
- **Future revisit conditions:** A product requirement for sub-minute/streaming data, or
  cross-service choreography that outgrows the orchestrator, opens this gate (doc 15).
- **Related documents:** [03 System Architecture](03-system-architecture.md), [16 Data Orchestration & Freshness](16-data-orchestration-and-freshness.md).

### ADR-0011 · Defer microservice extraction
- **Status:** Accepted (deferral)
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** Microservices solve organizational and scaling problems that a 1–3 person team
  at pre-scale does not have. Their costs (distributed transactions, network failure modes,
  deployment overhead) are immediate; their benefits are not.
- **Decision:** **Do not extract services now.** Build the modular monolith (ADR-0003) so that
  extraction is *possible*, and extract a module into its own service only when a specific
  scaling or team-boundary pressure demands it.
- **Alternatives:** (a) Microservices now — rejected as premature. (b) Monolith with no
  extraction path — rejected because it eventually traps the platform (see ADR-0003).
- **Trade-offs:** We forgo independent per-module scaling and deployment now. Module-owned
  schemas cost some boilerplate to preserve the option.
- **Consequences:** Complexity matches team size today; the escape hatch exists for tomorrow.
- **Future revisit conditions:** A module becomes a distinct scaling bottleneck; the team grows
  enough that independent deploy cadences matter; a module needs a different runtime/language.
- **Related documents:** [03 System Architecture](03-system-architecture.md).

### ADR-0012 · REST-first API as the single client contract
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect
- **Context:** The frontend (and any future client) needs one stable contract, decoupled from
  internal storage and analytics. The domain is read-heavy with stable nouns.
- **Decision:** Expose a **contract-first (OpenAPI), versioned REST/JSON API** as the *only*
  door to the platform. DTOs are projections of the domain model, deliberately decoupled from
  storage schemas. Lineage, freshness/staleness, and entitlement filtering are first-class at
  the edge.
- **Alternatives:** (a) GraphQL — flexible querying, but heavier to secure/cache/rate-limit and
  easy to let clients over-reach into internals. (b) gRPC — efficient, but poor fit for a
  browser-first read-heavy public API. (c) Direct DB/analytics access from the frontend —
  violates the layering (ADR-0002).
- **Trade-offs:** REST is chattier for complex graphs and requires deliberate endpoint design.
  We accept this for cacheability, simple auth/rate-limiting, and contract stability.
- **Consequences:** Internal refactors don't break clients. The static-JSON snapshot delivery is
  a transitional stand-in, superseded surface-by-surface (ADR-0020). Heavy analytics are async;
  caches must be entitlement-aware (audit condition C4).
- **Future revisit conditions:** If client needs become genuinely graph-shaped, evaluate adding
  a GraphQL gateway *over* the REST domain — not replacing the contract discipline.
- **Related documents:** [10 API Design](10-api-design.md).

### ADR-0013 · AI as a grounded consumer of analytics (defense-in-depth)
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** AI Systems Architect
- **Context:** A finance platform whose moat is traceability cannot ship a hallucinating
  chatbot. v1.0 overreached with a "no ungrounded claim can be surfaced" *guarantee*, which is
  unachievable with LLMs (blocker B8). Ungrounded AI and unvetted AI-extracted facts are the
  "plausible wrong number" nightmare.
- **Decision:** AI is a **consumer of analytics**, grounded via retrieval over the platform's
  own facts/results, with **defense-in-depth** (grounding-by-construction + provenance +
  faithfulness checks + mandatory labeling + a residual-risk register) — *not* a guarantee.
  AI-extracted facts enter as **`candidate` tier** and never become authoritative without
  corroboration or human confirmation. LLM vendors sit behind a swappable port gated by an eval
  suite.
- **Alternatives:** (a) Ungrounded generative chatbot — rejected, incompatible with the moat.
  (b) Claim zero hallucination — rejected as dishonest and unenforceable. (c) No AI — forgoes a
  real product capability.
- **Trade-offs:** AI answers are constrained to what the platform can cite; extraction requires
  a promotion path; eval infrastructure is real work. We accept limited scope for trustworthiness.
- **Consequences:** AI amplifies trustworthy analytics instead of undermining them. Honest
  labeling becomes the compliance posture (ADR-0018). Costs are budgeted with circuit-breakers.
- **Future revisit conditions:** A material advance in model faithfulness/verifiability could
  loosen candidate-tier rules; a new capability (agentic actions) requires a fresh ADR, not an
  amendment here.
- **Related documents:** [09 AI Framework](09-ai-framework.md).

### ADR-0014 · Analytics as uniform, versioned, traced engines
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Quantitative Systems Architect
- **Context:** Analytics is where the platform creates value and where wrong or unexplainable
  numbers do the most damage. Eleven product pillars risk becoming eleven inconsistent silos.
- **Decision:** Every analytics engine obeys **one contract**: typed inputs, a pure
  deterministic core, versioned methodology, and a **traced `AnalyticResult` envelope** (value,
  units, inputs, feature/formula/reference versions, quality flags, lineage). Engines consume
  **only features and other engines' results** — repository access lives solely in the feature
  layer (the v1.0 escape hatch is closed). No engine returns a bare number.
- **Alternatives:** (a) Ad-hoc per-feature analytics — fast, but inconsistent and untraceable.
  (b) A one-size "scoring pipeline" — rejected (ADR-0015).
- **Trade-offs:** More structure per engine; a feature must be defined for any canonical input
  an engine needs. We accept ceremony for determinism, reproducibility, and uniform lineage.
- **Consequences:** Every metric is reproducible and explainable by construction. As-of
  evaluation is framework-enforced, making backtests lookahead-free (with ADR-0017/knowledge_time
  capture, audit condition C1).
- **Future revisit conditions:** If the envelope proves insufficient for a new analytic class,
  extend it additively (owned by doc 04, ADR-0004).
- **Related documents:** [08 Analytics Framework](08-analytics-framework.md).

### ADR-0015 · Scoring is one module, not the core
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Quantitative Systems Architect
- **Context:** It is tempting — and common in retail tools — to make "the score" the center of
  the platform. Doing so privileges one opinionated output and couples everything to it,
  contradicting the research-terminal identity (ADR-0001).
- **Decision:** **Scoring is one analytics engine among many.** A `Score` is just one
  `AnalyticResult` type. The domain model must not privilege it: *removing scoring must be a
  no-op on core entities and other engines.*
- **Alternatives:** (a) Score-centric architecture — simple and marketable, but reductive and
  architecturally corrosive. (b) No scoring — forgoes a feature users want.
- **Trade-offs:** We forgo the simplicity of a single headline number as the organizing
  principle. We accept that scoring competes for attention with valuation, risk, screening, etc.
- **Consequences:** The platform stays a general research tool. "Delete scoring = no-op" is a
  testable model property (doc 04 completion criteria).
- **Future revisit conditions:** Revisit only if ADR-0001 (product philosophy) is itself
  revisited.
- **Related documents:** [01 Vision](01-vision.md), [08 Analytics Framework](08-analytics-framework.md).

### ADR-0016 · Decimal arithmetic for money
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** The prototype used binary floats throughout. Floating-point money accumulates
  representation error and rounding drift — unacceptable in a financial system and an
  instant-reject for any Stripe-class reviewer (blocker B5).
- **Decision:** **Monetary values use decimal arithmetic** with defined per-currency precision
  and rounding; binary float is permitted **only** for statistical quantities (returns,
  volatilities, ratios, simulation outputs). A shared Quantity type makes float-money
  unrepresentable, not merely discouraged.
- **Alternatives:** (a) Floats everywhere — fast/simple, but wrong for money. (b) Integer minor
  units everywhere — precise, but awkward for multi-currency and ratios.
- **Trade-offs:** Decimal is slower and more verbose than float; a declared decimal→float
  conversion seam is required at feature ingress (audit condition C3). We accept this for
  monetary correctness.
- **Consequences:** Money is exact end-to-end (at rest, in domain, at API); parity tests compare
  money exactly and statistics within tolerance (doc 11).
- **Future revisit conditions:** None foreseen; this is a correctness invariant, not a
  performance trade to revisit.
- **Related documents:** [02 Principles](02-engineering-principles.md), [04 Canonical Domain Model](04-canonical-domain-model.md).

### ADR-0017 · First-class lineage with three guarantee tiers
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Principal Data Architect
- **Context:** Lineage is the product moat, but v1.0 conflated "traceable to raw" with
  "reproducible as shown" (blocker B1). Reproducing what a user saw requires pinning not just
  formulas but the reference data and policies in effect at compute time.
- **Decision:** Lineage is a **first-class stored structure** (not logs) with **three declared
  guarantee tiers**: *traceable* (all values), *recomputable* (all derived values, within
  retention), and *bit-reproducible* (audited surfaces, by pinning code + formula + an
  effective-dated snapshot of reference data and policy). Reference data and policies are
  themselves versioned, effective-dated inputs. Lineage is stored at batch granularity for bulk
  runs and value granularity for served/audited surfaces.
- **Alternatives:** (a) Log-based lineage — cheap, but not queryable or guaranteeable. (b) One
  uniform ultra-fine tier — honest but prohibitively expensive at screen-scale cardinality.
- **Trade-offs:** Storage and write-path cost; discipline to pin reference state on every
  normalization/analytic run. We accept this as the price of the differentiator.
- **Consequences:** Audits can reconstruct "what we showed, from what data, under which
  methodology, when." The lineage store doubles as doc 16's invalidation dependency graph.
- **Future revisit conditions:** If lineage storage cost outpaces value at scale, revisit
  granularity/rollup policy — never the existence of stored lineage.
- **Related documents:** [02 Principles](02-engineering-principles.md), [05 Market Data Architecture](05-market-data-architecture.md), [07 Database Design](07-database-design.md).

### ADR-0018 · Compliance and lifecycle designed in from day one
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** FinTech CTO
- **Context:** v1.0 mandated append-only-immutable storage while promising retention limits and
  (by law) user erasure — a direct contradiction (blocker B2). India's **DPDP Act 2023** (the
  core users are Indian retail investors) and **GDPR** grant erasure rights that "keep forever"
  violates.
- **Decision:** Reconcile immutability with law via a **data-lifecycle + entitlements model**:
  "append-only" means no in-place mutation, *not* no end of life. Every dataset has a **retention
  class**; erasure uses **crypto-shredding** (object storage) and **tombstoning** (relational)
  so lineage *structure* survives while content is lawfully removed. A single **entitlements
  engine** (`tier × license × field × delay`) enforces data rights at exactly two points (API
  edge, AI layer). DPDP/GDPR are named regimes; the no-advice boundary is architectural.
- **Alternatives:** (a) Retrofit compliance later — cheaper now, catastrophic as data
  accumulates and regulators engage. (b) Append-only forever — clean, but illegal.
- **Trade-offs:** Lifecycle machinery, key management, and entitlement checks add complexity to
  storage and serving. We accept this to be lawful and auditable by design.
- **Consequences:** Data-subject requests are bounded, auditable operations. Caches must be
  entitlement-aware (audit condition C4). Some counsel-gated questions (DPDP localization) remain
  owned by doc 14.
- **Future revisit conditions:** New jurisdictions/regulations, or a regulatory reclassification
  of the platform's outputs, trigger a fresh ADR.
- **Related documents:** [13 Security](13-security.md), [14 Compliance & Licensing](14-compliance-and-licensing.md), [17 Entitlements & Data Governance](17-entitlements-and-data-governance.md).

### ADR-0019 · Commercial data strategy: eval feeds now, licensed feeds before monetization
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** FinTech CTO
- **Context:** The platform currently uses free/eval-grade feeds (yfinance, Alpha Vantage free
  tier, NSE). These are fine for a prototype but are **not** commercial redistribution licenses.
  The strangler approach (ADR-0020) keeps a public product live on these feeds for several
  phases (audit condition C2).
- **Decision:** Provider abstraction (ADR-0005) exists precisely so that **swapping to
  commercial-grade licensed feeds is an adapter change, not a re-architecture.** Licensed feeds
  are a **hard gate before commercial launch/monetization**; interim public-free operation on
  eval-grade feeds is a **named, dated, accepted risk** owned in doc 14, and any monetization
  advances the licensed-feed gate to that moment.
- **Alternatives:** (a) License commercial feeds now — correct terms, but heavy cost before
  product-market fit. (b) Launch commercially on free feeds — fast, but a licensing breach.
- **Trade-offs:** We carry a known interim compliance exposure (documented, time-boxed) and defer
  data cost, in exchange for validating the product before paying for feeds.
- **Consequences:** Licensing terms live as adapter metadata feeding the entitlements engine
  (ADR-0018). The commercial-feed swap is de-risked by the port contract.
- **Future revisit conditions:** Any monetization event, a public-scale usage jump, or a vendor
  terms change opens the licensed-feed gate immediately.
- **Related documents:** [06 Provider Abstraction Layer](06-provider-abstraction-layer.md), [14 Compliance & Licensing](14-compliance-and-licensing.md).

### ADR-0020 · Walking Skeleton first; strangle the prototype
- **Status:** Accepted
- **Date:** 2026-07-17
- **Deciding role:** Chief Software Architect / FinTech CTO
- **Context:** v1.0's foundation-first roadmap delivered **zero user value until Phase 4** — a
  business risk masquerading as engineering discipline (blocker B12). A large architecture also
  carries integration risk that only reveals itself end-to-end.
- **Decision:** Build a **Walking Skeleton first** (Phase 0.5): the thinnest end-to-end slice —
  5 instruments, 1 provider, 1 metric, 1 endpoint, wired to the live frontend — exercising every
  layer in weeks, and **timing the recompute-from-raw RTO**. Keep the existing prototype **live
  as the product** and **strangle it surface-by-surface** as real endpoints replace snapshot
  JSON.
- **Alternatives:** (a) Big-bang foundation then cutover (v1.0) — clean, but months of no value
  and a risky single cutover. (b) Keep iterating the prototype without the foundation —
  perpetuates the technical debt the blueprint exists to escape.
- **Trade-offs:** The skeleton's one endpoint is a deliberate, disposable exception to
  "no API before the domain model," re-cut on the hardened model. We accept a little throwaway
  work to de-risk the whole stack and keep value continuous.
- **Consequences:** Integration risk is retired early; users are retained throughout; the
  recompute RTO becomes a measured number (doc 12). Heavy machinery (router, price
  bitemporality, TSDB) lands only at its gate.
- **Future revisit conditions:** If the skeleton reveals a foundational assumption is wrong,
  amend the relevant doc/ADR before widening — that is the skeleton's purpose.
- **Related documents:** [15 Development Roadmap](15-development-roadmap.md).

---

## Decision log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-17 | ADR framework established; ADR-0001…0020 recorded as Accepted, capturing the decisions approved in Architecture v2.0. | Create a permanent, immutable architectural memory distinct from the living specification. Next ID: ADR-0021. |
