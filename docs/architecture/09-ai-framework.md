# 09 · AI Framework

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blocker B8: zero-hallucination guarantee replaced with defense-in-depth; candidate/authoritative tiers; phased RAG corpus; budget & model-swap governance; entitlements consultation (doc 17) |
| **Owner** | AI Systems Architect |
| **Depends on** | [08 Analytics Framework](08-analytics-framework.md) |
| **Consumed by** | 10, 11, 13, 14 |

## Purpose
Define how AI is integrated so that it *amplifies* the trustworthy analytics beneath it
instead of undermining them. AI **consumes analytics** (principle 3); it never invents facts,
never reaches into raw providers or the database, and never crosses the no-advice line (doc 14).

## Why it exists
A finance platform whose differentiator is *traceability* cannot bolt on a hallucinating
chatbot. The prototype's direct "ticker → LLM → prose" call (`ai_analysis.py`) is the
anti-pattern: ungrounded, unverifiable, provider-locked. This document replaces it with a
retrieval-grounded, guard-railed, provider-abstracted AI layer.

## Decisions this document owns

### The grounding stance: defense-in-depth, not a guarantee (v2.0, per review B8)
v1.0 claimed "no ungrounded claim can be surfaced." The review correctly rejected this: LLM
faithfulness checks are probabilistic, so a *zero*-hallucination guarantee is unachievable and
claiming it is itself a trust defect. v2.0 replaces the guarantee with layered defenses plus
honest labeling:
- **Grounding-by-construction:** AI answers are composed from `AnalyticResult`s and canonical
  facts retrieved from the platform (docs 04/07/08) — never from the model's parametric memory
  of a company. Retrieval is the only sanctioned fact source.
- **Provenance on every claim:** generated statements link to the analytic results/documents
  used, so citations work like a numeric metric's lineage — and are *human-verifiable*, which
  is the real safety property.
- **Post-generation faithfulness checks** score claims against cited sources; failing content
  is suppressed or visibly flagged — reducing, not eliminating, ungrounded output.
- **Mandatory AI-content labeling** (doc 14): every AI-generated statement is labeled as such,
  with its confidence caveats. The user is never led to mistake generated prose for verified
  data.
- **A residual-risk register:** known failure modes (subtle misquotation, wrong aggregation of
  correct facts, stale-context reasoning) are documented, measured by the doc 11 eval suite,
  and tracked with thresholds — managed risk, not assumed perfection.
- **AI is a consumer, not a source.** It cannot write canonical data, cannot call providers,
  cannot bypass analytics. Its only inputs are the platform's own outputs plus the user's
  question — filtered by the caller's **entitlements (doc 17)**: the assistant can never
  surface data its user could not query directly.

### Capability decomposition (modules, mirroring the pillars)
- **Retrieval / RAG layer — with a phased corpus (v2.0, per review).** The corpus starts as
  the platform's *own* outputs: canonical facts, analytic results, and the methodology catalog
  (doc 08) — all already lineage-carrying. **Filings/news ingestion is a separately scoped
  programme** (document pipeline, parsing, entity-linking, its own licensing questions), not a
  bullet-point assumption; it lands per doc 15, and until it does the AI cites only what the
  platform already trusts. Retrieval is the *only* sanctioned way AI gets facts.
- **Research assistant** — natural-language interface that composes analytics and explains
  results, with citations. Conversation is *an interface to the platform*, not a standalone
  brain (honors doc 01 non-goal "not a chatbot").
- **Narrative/explanation generation** — turning `AnalyticResult`s into readable, cited prose
  ("earnings analysis," "financial-health summary") — the legitimate successor to the
  prototype's 3-statement feature, now grounded and sourced.
- **Structured extraction — candidate tier only (v2.0, per review B8).** AI-parsed
  `FundamentalFact`s enter the domain stamped **`candidate`** (doc 04 authority tiers) — range
  validation alone cannot vouch for an LLM's reading of a filing; a plausible-but-wrong number
  that passes range checks is exactly the defect this platform exists to prevent. Promotion to
  `authoritative` requires corroboration by a second independent source or explicit human
  confirmation (doc 05). Candidate facts are never served as authoritative and never feed
  authoritative analytics. AI proposes; the data pipeline disposes.

### Model & provider abstraction (principle 7/8 for AI)
- **LLM providers sit behind an AI port**, exactly like data providers behind doc 06.
  Groq/Llama, or any other model, is a swappable adapter; no app code names a model vendor.
- **Model swap is gated by behavior, not just interface (v2.0, per review).** Swapping or
  upgrading a model requires passing the doc 11 AI eval suite within declared regression
  thresholds (grounding, faithfulness, no-advice, injection resistance). Interface
  compatibility alone does not authorize a swap.
- **Model outputs are treated as untrusted** until grounded/validated — prompt-injection from
  retrieved documents is an explicit threat (doc 13).

### Guardrails & safety (owned jointly with docs 13/14)
- **No personalized investment advice.** The AI explains *quantitative, general* analysis and
  is constrained (system policy + output checks) from issuing individualized buy/sell/hold
  recommendations — this is an architectural constraint, not a disclaimer footnote (doc 14).
- **Grounding/faithfulness checks** — responses are checked against their cited sources;
  unsupported claims are suppressed or flagged.
- **Determinism & auditability where it matters.** Prompts, retrieved context, model+version,
  and outputs are logged for audit and evaluation; user-facing AI results are cache-able and
  reproducible enough to investigate complaints.
- **Cost/latency governance is mandatory, not aspirational (v2.0).** AI runs in the analytics
  plane (doc 03), pre-computed where possible; every AI surface has a declared per-user and
  per-platform **budget with circuit-breakers** (requests, tokens, spend) enforced at the API
  edge (doc 10) and monitored as first-class telemetry (doc 12). Open-ended AI cost is a
  production incident class, not a surprise invoice.

## What must NOT live here
- The analytics/formulas the AI consumes — doc 08.
- The API surface for AI features — doc 10.
- The legal/regulatory basis of the no-advice line — doc 14 (this doc *enforces* it technically).
- Secrets handling for model keys, injection defenses in depth — doc 13.

## Dependencies
- [08 Analytics Framework](08-analytics-framework.md) — the AI's factual substrate.
- [14 Compliance & Licensing](14-compliance-and-licensing.md) — the no-advice / disclosure rules.
- [13 Security](13-security.md) — prompt-injection, secrets, data-egress controls.

## Completion criteria
- [ ] Defense-in-depth grounding is specified end-to-end (construction, provenance,
      faithfulness checks, labeling) with a maintained residual-risk register — no
      zero-hallucination claims anywhere in the doc set.
- [ ] LLM providers are abstracted behind a port; no vendor named in app code; model swaps
      gated by eval-suite thresholds.
- [ ] The no-advice boundary is implemented as a constraint, not just wording.
- [ ] AI-extracted data enters as `candidate` tier and cannot reach authoritative surfaces
      without corroboration or human confirmation.
- [ ] The RAG corpus is phased; filings/news ingestion is separately scoped.
- [ ] AI budgets/circuit-breakers are declared per surface; prompts/context/outputs are
      auditable and evaluable (doc 11).
- [ ] AI retrieval and responses respect caller entitlements (doc 17).
