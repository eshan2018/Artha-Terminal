# Implementation · 01 · Engineering Decision Log (ED)

| | |
|---|---|
| **Status** | Living — implementation tier (not part of the frozen architecture set) |
| **Owner** | Implementing engineer / Chief Software Architect |
| **Governed by** | Architecture v2.0 (`docs/architecture/`, APPROVED & FROZEN 2026-07-17) |
| **Complements** | [ADR registry — doc 18](../architecture/18-architecture-decision-records.md). **This log does not replace it.** |

## Purpose
Record **implementation-level decisions that do not meet the ADR threshold** — the concrete
technologies, versions, frameworks, libraries, hosted services, and tooling that *realize* the
approved architecture without changing it. These are the decisions Architecture v2.0 deliberately
left to implementation.

## The ADR / ED boundary (the classification rule)
A decision is an **ADR** (goes in [doc 18](../architecture/18-architecture-decision-records.md)) if it changes the system architecture,
architectural boundaries, public contracts, long-term maintainability, or deployment model — or
would require a *migration of the architecture* if reversed.

A decision is an **Engineering Decision (ED)** (goes here) if it is an implementation detail —
language version, framework, library, tooling, testing framework, hosted-service/vendor
selection, package choice — that does **not** alter the approved architecture. Reversing an ED
is a *re-implementation of the same architecture*, not a migration of it.

> **Litmus used throughout:** in each domain below, the *architectural* decision is already
> owned by an ADR or an architecture document (e.g. PostgreSQL-as-engine = ADR-0008; REST-as-
> contract = ADR-0012; orchestration-model = doc 16; single-cloud-stance = doc 12). Each ED
> records only the residual *realization* under that already-made architectural decision. If a
> proposal instead **replaced** the architectural decision (e.g. "use a non-Postgres engine"),
> it would require an ADR that supersedes the relevant one — not an ED.

## ED lifecycle
`Proposed` → `Accepted` → (`Superseded by ED-NNN` | `Deprecated`).
EDs are **mutable** in a way ADRs are not: because they don't bind the architecture, an ED may
be revised in place for non-material corrections, and superseded (new ID) for a material change
of selection. An ED is **never promoted to an ADR**; if a reversal turns out to require an
architectural change, that is a *new ADR*, and the ED is marked `Superseded`/`Deprecated`.

## ED template
```markdown
### ED-NNN · <Title>
- **Status:** Proposed | Accepted | Superseded by ED-MMM | Deprecated
- **Context:** the need and the constraints from the architecture.
- **Decision:** the concrete selection.
- **Alternatives Considered:** options weighed and not chosen.
- **Consequences:** what follows; reversal cost; what stays swappable.
- **Configuration Source:** the file(s) that are the authoritative, enforceable record.
- **Related Architecture Documents:** the ADR/doc whose decision this ED realizes.
```

## Rules
1. **One selection per ED.** Split bundled choices.
2. **An ED never contradicts the architecture.** If it seems to, the architecture wins and the
   ED is wrong.
3. **The Configuration Source is authoritative for reproducibility.** The prose here explains
   *why*; the config file is the *what* that CI/deploys actually consume.
4. **No duplication with ADRs.** An ED cites the ADR it realizes; it does not re-decide it.
5. **IDs are permanent and never reused;** next id is **ED-011**.

---

## ED Index
| ID | Title | Status | Realizes |
|----|-------|--------|----------|
| [ED-001](#ed-001--backend-language--runtime) | Backend language & runtime — Python 3.12 | Accepted | ADR-0014/0016, doc 12 |
| [ED-002](#ed-002--api-framework) | API framework — FastAPI + Pydantic | Accepted | ADR-0012, doc 10 |
| [ED-003](#ed-003--postgresql-deployment-realization) | PostgreSQL realization — `MarketDataRepository` port; SQLite dev backend, Postgres in prod | Accepted (rev. 2026-07-17) | ADR-0008, doc 07/12 |
| [ED-004](#ed-004--object-storage-realization) | Object-storage realization — `RawStore` port; filesystem dev backend, S3 in prod | Accepted (rev. 2026-07-17) | ADR-0009, doc 07/17 |
| [ED-005](#ed-005--orchestrator-product) | Orchestrator product | Proposed | doc 16, ADR-0010 |
| [ED-006](#ed-006--backend-cloud-vendor) | Backend cloud vendor | Proposed | doc 12 |
| [ED-007](#ed-007--test-framework) | Test framework — pytest | Accepted | doc 11 |
| [ED-008](#ed-008--architecture-guardrail-implementation) | Architecture guardrail lints — custom AST checks | Accepted | doc 03/06, ADR-0002/0003/0005 |
| [ED-009](#ed-009--linterformatter) | Linter/formatter — ruff | Accepted | doc 11 |
| [ED-010](#ed-010--property-based-testing-library) | Property-based testing — hypothesis (dev-only) | Accepted | doc 11 (B10) |

---

### ED-001 · Backend language & runtime
- **Status:** Accepted
- **Context:** The backend (L1–L9) needs a primary language. The prototype's proven analytics
  math lives in `shared/calculations.py` (pure pandas/NumPy); the domain requires exact decimal
  money ([ADR-0016](../architecture/18-architecture-decision-records.md#adr-0016--decimal-arithmetic-for-money)). The architecture is language-agnostic at its boundaries, so this is a
  realization choice, not an architectural one.
- **Decision:** **Python 3.12** as the single primary backend language.
- **Alternatives Considered:** *TypeScript/Node* (unifies with the frontend, but forces
  re-implementing proven math and has weaker decimal/numeric ergonomics); *Go/Rust* (performance
  the current scale does not need, at the cost of discarding the math and slowing iteration);
  *Java/Kotlin* (heavier ecosystem, no benefit here).
- **Consequences:** The prototype's math is *ported behind* the engine contract, not lifted
  verbatim ([ADR-0014](../architecture/18-architecture-decision-records.md#adr-0014--analytics-as-uniform-versioned-traced-engines)); money uses `decimal.Decimal` ([ADR-0016](../architecture/18-architecture-decision-records.md#adr-0016--decimal-arithmetic-for-money)). The frontend stays TypeScript
  (separate concern). Reversal is a full re-implementation of the *same* architecture — expensive
  but not an architectural migration (no boundary/contract/schema changes), which is precisely
  why this is an ED and not an ADR.
- **Configuration Source:** `.python-version`, `pyproject.toml` (`requires-python = ">=3.12"`).
- **Related Architecture Documents:** [ADR-0016](../architecture/18-architecture-decision-records.md#adr-0016--decimal-arithmetic-for-money), [ADR-0014](../architecture/18-architecture-decision-records.md#adr-0014--analytics-as-uniform-versioned-traced-engines), [doc 12](../architecture/12-deployment-strategy.md).

### ED-002 · API framework
- **Status:** Accepted
- **Context:** [ADR-0012](../architecture/18-architecture-decision-records.md#adr-0012--rest-first-api-as-the-single-client-contract) fixes the public contract as versioned, contract-first REST with typed
  DTOs. A Python framework must realize that contract; the framework itself is interchangeable
  behind it.
- **Decision:** **FastAPI (ASGI) + Pydantic v2** — typed DTOs, generated OpenAPI, native async.
- **Alternatives Considered:** *Flask* (mature but manual validation/OpenAPI); *Django REST
  Framework* (heavy, ORM-centric — tension with module-owned repositories, [ADR-0003](../architecture/18-architecture-decision-records.md#adr-0003--modular-monolith-with-module-owned-schemas)); *Litestar*
  (a viable equivalent, smaller ecosystem).
- **Consequences:** OpenAPI is generated (satisfies contract-first, [doc 10](../architecture/10-api-design.md)); DTOs are Pydantic
  projections of the domain, decoupled from storage; async supports doc 10's async-heavy-analytics
  rule. The framework is swappable behind the REST/OpenAPI contract without client impact.
- **Configuration Source:** `pyproject.toml` dependencies; the OpenAPI spec artifact.
- **Related Architecture Documents:** [ADR-0012](../architecture/18-architecture-decision-records.md#adr-0012--rest-first-api-as-the-single-client-contract), [doc 10](../architecture/10-api-design.md).

### ED-003 · PostgreSQL deployment realization
- **Status:** Accepted *(revised 2026-07-17; production vendor finalized at first deploy)*
- **Context:** [ADR-0008](../architecture/18-architecture-decision-records.md#adr-0008--postgresql-as-the-primary-system-of-record) fixes **PostgreSQL as the primary system of record** — architectural and
  unchanged. This ED records the *interface* and the *per-environment backend*. As with
  [ED-004](#ed-004--object-storage-realization), doc 12 provides distinct local/dev, staging and production environments, and
  standing up a database service to persist five instruments locally is disproportionate for a
  1–3 person team.
- **Decision:** A **`MarketDataRepository` port** is the interface — application code never
  touches a driver (doc 07 portability rule). Backends: **dev/CI = SQLite** via the Python
  **standard library** (`sqlite3`: zero dependencies, no service, no Docker);
  **production = managed PostgreSQL 16**, partition-capable, single vendor selected at deploy
  (Neon, Supabase, RDS/Aurora, Cloud SQL) per managed-first. The **schema shape is identical
  across both** (`backend/domain/market_data/schema.py`): module-owned tables, the
  `knowledge_time` version axis in the primary key, and a `CHECK` constraint making an
  index-level-with-a-currency unstorable. Money is stored as **exact text** in SQLite and as
  `NUMERIC` in PostgreSQL — never as a binary float in either.
- **Alternatives Considered:** *Postgres via docker-compose now* (literal compliance and
  exercises the real engine, but adds Docker + a service + a driver dependency and makes CI
  non-hermetic — disproportionate at this scale); *an in-memory repository* (smallest, but
  defers the substantive work — schema, DDL, exact round-trip, durability — and would prove
  nothing about persistence); *a non-Postgres engine in production* (out of scope — that would
  **supersede ADR-0008** and require an ADR, not an ED).
- **Consequences:** Zero new dependencies; CI stays hermetic and fast; real DDL, a real schema
  and real durability are exercised now. The port keeps Postgres a drop-in — a second
  implementation, not an application change. **Accepted costs:** SQL dialect differences must be
  absorbed by the Postgres implementation (notably `TEXT`→`NUMERIC` for money and native
  partitioning, neither exercised until deploy), and Postgres-specific behaviour (concurrency,
  connection pooling, partition pruning) is unproven until then. Escalation to a dedicated TSDB
  remains gated (ADR-0008).
- **Configuration Source:** `backend/domain/market_data/repository.py` (the port),
  `backend/domain/market_data/sqlite_repository.py` (dev/CI backend),
  `backend/domain/market_data/schema.py` (the schema); IaC/Terraform + secret store for the
  production instance, added at deploy.
- **Related Architecture Documents:** [ADR-0008](../architecture/18-architecture-decision-records.md#adr-0008--postgresql-as-the-primary-system-of-record), [ADR-0003](../architecture/18-architecture-decision-records.md#adr-0003--modular-monolith-with-module-owned-schemas), [doc 04](../architecture/04-canonical-domain-model.md), [doc 07](../architecture/07-database-design.md), [doc 12](../architecture/12-deployment-strategy.md).

### ED-004 · Object-storage realization
- **Status:** Accepted *(revised 2026-07-17; production vendor finalized at first deploy)*
- **Context:** [ADR-0009](../architecture/18-architecture-decision-records.md#adr-0009--object-storage-for-immutable-raw-capture-and-deep-history) fixes **object storage for immutable raw capture** — raw is never in the
  hot relational store and never discarded. That is architectural and unchanged. This ED records
  the *interface* and the *per-environment backend*. Standing up MinIO/Docker/boto3 to capture
  five instruments locally is disproportionate for a 1–3 person team, and doc 12 explicitly
  provides distinct local/dev, staging and production environments with environment-injected
  backing services.
- **Decision:** A provider-neutral **`RawStore` port** (append-only, immutable objects, portable
  keys, prefix listing) is the interface — *not* a vendor SDK. Backends:
  **dev/CI = `FilesystemObjectStore`**, a first-class reference implementation of that port;
  **production = a managed S3-compatible object store** (ADR-0009), added as a second
  implementation at first deploy. The **object-key layout is backend-independent** and maps 1:1
  onto S3 keys — `raw/v1/{provider}/{dataset}/{window}/{instrument}/{payload_sha256}.json` —
  with `{window}` as the per-source-window **crypto-shred scope** (doc 17/13).
- **Alternatives Considered:** *MinIO via docker-compose now* (literal compliance and exercises
  the S3 path, but adds Docker + a service + boto3, slows the local loop, and makes CI
  non-hermetic — disproportionate at this scale); *write both backends now* (S3 fidelity on
  demand, but writes S3 code before it is needed and doubles maintenance from day one);
  *raw in Postgres* (rejected by ADR-0009 — would require a superseding ADR).
- **Consequences:** Zero new dependencies or infrastructure; CI stays hermetic and fast. The
  port keeps the S3 backend a drop-in — swapping it changes one module, not the application.
  Append-only/immutable semantics and the shred-scope prefix are preserved, so lawful erasure
  remains feasible without architectural change. **Accepted costs:** the S3 code path is not
  exercised until first deploy (deferring discovery of SDK/auth/consistency issues), and the
  Phase 0.5 recompute-from-raw timing is a **local filesystem baseline, not object-storage
  evidence** — it must be labelled as such and re-measured against real object storage at first
  deploy (doc 12 already requires re-measurement as volume grows).
- **Configuration Source:** `backend/ingestion/raw_store.py` (the port),
  `backend/ingestion/filesystem_object_store.py` (dev/CI backend),
  `backend/ingestion/raw_capture.py` (key layout); IaC/Terraform + secret store for the
  production bucket, added at deploy.
- **Related Architecture Documents:** [ADR-0009](../architecture/18-architecture-decision-records.md#adr-0009--object-storage-for-immutable-raw-capture-and-deep-history), [doc 05](../architecture/05-market-data-architecture.md), [doc 07](../architecture/07-database-design.md), [doc 12](../architecture/12-deployment-strategy.md), [doc 17](../architecture/17-entitlements-and-data-governance.md).

### ED-005 · Orchestrator product
- **Status:** Proposed *(the most architecture-adjacent ED — document any change carefully)*
- **Context:** [doc 16](../architecture/16-data-orchestration-and-freshness.md) fixes the **orchestration model** (declared DAGs, idempotent keyed tasks,
  the invalidation protocol) and explicitly states *the specific product is a selection*. This ED
  records that product.
- **Decision:** Recommend **Dagster** (asset-oriented; its asset graph maps naturally onto doc
  16's derived-data dependency graph and future invalidation wiring; strong local-dev story),
  used in its **minimal** form for the Walking Skeleton's single forward-only DAG.
- **Alternatives Considered:** *Temporal* (durable workflows, very powerful but heavier and
  steeper; a stronger fit only if/when an event-driven backbone is later un-gated, [ADR-0010](../architecture/18-architecture-decision-records.md#adr-0010--defer-the-event-bus));
  *Prefect* (lightweight, flexible; weaker asset/lineage alignment); *ad-hoc cron/scripts*
  (rejected — [doc 16](../architecture/16-data-orchestration-and-freshness.md) forbids undeclared cron above the skeleton).
- **Consequences:** The asset model aligns the orchestrator with the doc-16 dependency graph,
  easing Phase-2 invalidation. **Reversal cost is real but bounded** (re-expressing DAGs), which
  is why this is flagged as the ED to change most deliberately — but it remains an ED because the
  *model* it serves is already architectural (doc 16), unchanged by the product.
- **Configuration Source:** orchestrator project/workspace config; deployment config.
- **Related Architecture Documents:** [doc 16](../architecture/16-data-orchestration-and-freshness.md), [ADR-0010](../architecture/18-architecture-decision-records.md#adr-0010--defer-the-event-bus), [doc 12](../architecture/12-deployment-strategy.md).

### ED-006 · Backend cloud vendor
- **Status:** Proposed *(vendor finalized at first deploy)*
- **Context:** [doc 12](../architecture/12-deployment-strategy.md) already fixes the **deployment-model stance** — single cloud on the
  critical path until a measured reason to diversify, managed-first, API on containers (not
  serverless edge). Those are architectural and approved. This ED records **only the vendor
  selection** under that stance.
- **Decision:** A **single backend cloud vendor**, TBD at deploy, chosen to co-host the managed
  Postgres (ED-003), object storage (ED-004), and orchestrator (ED-005) to minimize ops surface
  for a 1–3 person team. API runs on **containers**. The existing frontend stays on Vercel.
- **Alternatives Considered:** *Multi-cloud now* (rejected by the doc-12 stance until a measured
  need); *serverless-edge API* (rejected by doc 12 — the API is stateful/DB-connected).
- **Consequences:** Consolidating managed services with one vendor reduces operational load;
  portability escape hatches (SQL, S3 API, containers) are documented, not pre-built (principle
  18). A vendor change is a re-host of managed services, not an architectural migration.
- **Configuration Source:** IaC/Terraform; deployment/environment config.
- **Related Architecture Documents:** [doc 12](../architecture/12-deployment-strategy.md), [ADR-0008](../architecture/18-architecture-decision-records.md#adr-0008--postgresql-as-the-primary-system-of-record), [ADR-0009](../architecture/18-architecture-decision-records.md#adr-0009--object-storage-for-immutable-raw-capture-and-deep-history).

### ED-007 · Test framework
- **Status:** Accepted
- **Context:** Doc 11 mandates hermetic, reproducible tests across several tiers (unit,
  contract, integration, guardrail). A Python test runner is needed from M1.
- **Decision:** **pytest** (+ **pytest-cov** for targeted coverage), pinned in `pyproject.toml`.
- **Alternatives Considered:** *stdlib `unittest`* (works, but weaker fixtures/parametrization
  and no ecosystem for property/contract tiers later); *nose2* (effectively unmaintained).
- **Consequences:** Fixtures/parametrization suit the guardrail and (later) property-based and
  contract tiers ([doc 11](../architecture/11-testing-strategy.md)); coverage is targeted, not vanity (principle 18). Runner is
  swappable — tests are plain assertions.
- **Configuration Source:** `pyproject.toml` (`[project.optional-dependencies] dev`,
  `[tool.pytest.ini_options]`, `[tool.coverage.run]`).
- **Related Architecture Documents:** [doc 11](../architecture/11-testing-strategy.md).

### ED-008 · Architecture guardrail implementation
- **Status:** Accepted
- **Context:** Doc 03/06 and ADR-0002/0003/0005 require CI to fail on an upward import, a
  vendor name above L1, or a cross-module schema read. An enforcement mechanism is needed.
- **Decision:** **Custom, stdlib-only AST checks** in `tools/ci/` (dependency-direction,
  no-vendor-above-L1, module-schema-isolation), driven by a single machine-readable
  `architecture_map.py`.
- **Alternatives Considered:** *import-linter* (good for layer contracts, but does not express
  the vendor-token or module-owned-schema rules, and adds a dependency + config dialect);
  *pydeps/grimp alone* (visualization, not enforcement); *hand review* (rejected — the whole
  point is that the rule is structural, not discretionary).
- **Consequences:** One dependency-free source of truth for the layer graph; the vendor and
  schema rules are first-class; the checks run anywhere with no third-party install. Trade-off:
  we maintain ~150 lines of lint code (covered by its own tests).
- **Configuration Source:** `tools/ci/architecture_map.py` (the rules); `tools/ci/*.py` (the
  checks); `deploy/ci.workflow.yml` + `Makefile` (invocation — see that file's
  activation note; it mirrors `deploy/snapshots.workflow.yml`).
- **Related Architecture Documents:** [doc 03](../architecture/03-system-architecture.md), [doc 06](../architecture/06-provider-abstraction-layer.md), [ADR-0002](../architecture/18-architecture-decision-records.md#adr-0002--strictly-layered-architecture-with-an-enforced-dependency-direction)/[0003](../architecture/18-architecture-decision-records.md#adr-0003--modular-monolith-with-module-owned-schemas)/[0005](../architecture/18-architecture-decision-records.md#adr-0005--provider-abstraction-via-portsadapters), [doc 11](../architecture/11-testing-strategy.md).

### ED-009 · Linter/formatter
- **Status:** Accepted
- **Context:** Consistent style and a fast import/order/bug lint keep the codebase reviewable.
- **Decision:** **ruff** (lint + import sorting), pinned in `pyproject.toml`.
- **Alternatives Considered:** *flake8 + isort + black* (three tools where one suffices);
  *pylint* (slower, noisier).
- **Consequences:** One fast tool; config lives in `pyproject.toml`; swappable (style only,
  no architectural weight).
- **Configuration Source:** `pyproject.toml` (`[tool.ruff]`, `[tool.ruff.lint]`).
- **Related Architecture Documents:** [doc 11](../architecture/11-testing-strategy.md).

### ED-010 · Property-based testing library
- **Status:** Accepted
- **Context:** [Doc 11](../architecture/11-testing-strategy.md) (hardened per review B10) makes property-based tests a **mandatory**
  tier for financial correctness — "the bugs no one thought to hand-compute" — alongside
  reference values and an independent reference implementation. M3 is the first milestone with
  financial math to test, so the mechanism is needed now. Doc 11 also requires the suite to stay
  hermetic with fixed seeds, which a randomized generator threatens by default.
- **Decision:** **hypothesis**, pinned in `pyproject.toml` under `[project.optional-dependencies] dev`,
  run under a `hermetic` profile (`derandomize=True`, `deadline=None`) registered in
  `backend/tests/conftest.py`.
- **Alternatives Considered:** *hand-rolled generators over `random.Random(seed)`* — zero new
  dependencies, but reimplements shrinking badly, and a minimal counterexample is most of what
  makes a failing property test actionable; *skip the tier* — rejected, doc 11 mandates it.
- **Consequences:** **Runtime dependencies remain zero** — this is dev-only, so nothing ships.
  `derandomize` makes a given commit always explore the same inputs, so failures are reproducible
  and green runs repeatable; `deadline=None` removes a wall-clock dependence masquerading as a
  correctness check. Reversal cost is low: the properties are plain assertions over generated
  lists and would survive a change of generator.
- **Configuration Source:** `pyproject.toml` (`[project.optional-dependencies] dev`);
  `backend/tests/conftest.py` (the hermetic profile).
- **Related Architecture Documents:** [doc 11](../architecture/11-testing-strategy.md); complements [ED-007](#ed-007--test-framework) (pytest).

---

## Change log
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-07-17 | Log created; ED-001…ED-006 recorded — the technology selections that realize Architecture v2.0, classified as implementation decisions (not ADRs) per the doc-18 threshold rule. | The six selections change no architectural boundary/contract/deployment-model; the architectural decisions they realize are already owned by ADR-0008/0009/0012/0014/0016 and docs 12/16. Keeps the ADR registry concise. |
| 2026-07-17 | **ED-007…ED-009 recorded** during Milestone M1 (test framework = pytest; guardrail lints = custom AST checks; linter/formatter = ruff). | M1 introduces and uses these tools; they are implementation/tooling details below the ADR threshold. |
| 2026-07-17 | **ED-003 revised** (Proposed → Accepted): interface is a `MarketDataRepository` port; dev/CI backend is stdlib SQLite; production remains managed PostgreSQL; one schema shape across both. | Same environment reasoning as ED-004: ADR-0008 fixes the **deployed** system of record; the local backend is ED-tier. SQLite is stdlib, so it adds zero dependencies and no Docker while still exercising real DDL, schema, exact-decimal round-trip and durability. Accepted cost recorded: SQL dialect differences and Postgres-specific behaviour unproven until deploy. |
| 2026-07-17 | **ED-004 revised** (Proposed → Accepted): interface is a provider-neutral `RawStore` port; dev/CI backend is a first-class `FilesystemObjectStore`; production remains S3-compatible object storage; key layout is backend-independent and S3-mapping. | Governance review determined object storage is architectural **for the deployed platform** (ADR-0009, unchanged), while the per-environment backend is ED-tier (doc 12 distinct environments). Applies the minimalism principle: no Docker/MinIO/boto3 until first deploy. Accepted cost recorded: S3 path unexercised until deploy; skeleton RTO is a local baseline. |
| 2026-07-18 | **ED-010 recorded** during Milestone M3: hypothesis as the property-based testing library, dev-only, under a derandomized hermetic profile. | M3 is the first milestone with financial math, and doc 11 makes the property tier mandatory for it. Dev-only, so the zero-runtime-dependency position is unchanged. Next id: ED-011. |
