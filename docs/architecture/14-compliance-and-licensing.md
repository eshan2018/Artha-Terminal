# 14 · Compliance & Market Data Licensing

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 — amended per review blockers B2 (DPDP/GDPR named, lifecycle reconciled via doc 17) and B9 (entitlements mechanized in doc 17); attribution specifics + AI labeling |
| **Owner** | FinTech CTO |
| **Depends on** | [01 Vision](01-vision.md), [05 Market Data Architecture](05-market-data-architecture.md), [06 Provider Abstraction Layer](06-provider-abstraction-layer.md) |
| **Consumed by** | 05, 06, 09, 10, 13, 15, 17 |

## Purpose
Own the non-technical constraints that nonetheless *shape the architecture*: what data we are
legally permitted to store, cache, redistribute and to whom; and the regulatory posture around
delivering financial analytics to retail investors. These are designed in from day one
(principle 9), because they are architecturally load-bearing.

> **Note:** This document records engineering-facing constraints and the *questions that
> require qualified legal/compliance counsel*. It is not legal advice and does not substitute
> for it. Where it says "must be decided," that is a gate on real counsel before the relevant
> phase ships.

## Why it exists
Market-data licensing and financial-services regulation are the two forces most likely to
force an expensive rearchitecture if ignored. A provider's terms can forbid caching or
redistribution; a regulator can treat certain outputs as "advice." Building the platform so
these constraints are *enforceable switches* — not assumptions — is cheaper than retrofitting.

## Decisions this document owns

### Market-data licensing (the redistribution problem)
- **Every provider's license terms are captured as adapter metadata** (doc 06) and are
  *machine-actionable*: may we store it? cache it? for how long? may we redistribute to end
  users? derive from it? display raw vs. derived only? attribution required?
- **The architecture must be able to enforce "derived-only" or "no-redistribution" per
  source.** Because the platform separates raw capture (internal) from what the API serves
  (doc 10), it can be licensed to *compute on* data it is not licensed to *serve verbatim* —
  serving only derived analytics. This separation is a licensing feature, not just cleanliness.
- **Free/hobby feeds (yfinance, Alpha Vantage free tier, NSE) are personal/eval-grade, not a
  commercial redistribution license.** Their current use is fine for a prototype; **commercial
  operation requires properly licensed feeds**, and the provider-abstraction layer (doc 06)
  exists precisely so that swap is an adapter change, not a rearchitecture. This dependency is
  an explicit gate in the roadmap (doc 15).
- **Interim eval-feed exposure is a named, accepted risk (audit clarification C2).** The
  strangler roadmap (doc 15) keeps a **public, free** product live on eval-grade feeds through
  Phases 0.5–7. This interim exposure is **explicitly accepted and dated (2026-07-17), owned by
  the FinTech CTO, with a review date at the start of Phase 5** (first breadth expansion). Any
  **monetization of any kind advances the commercial-licensed-feed gate from Phase 8 to that
  moment** — paid access on eval-grade feeds is not permitted. See the counsel-gate list below.
- **Attribution, retention, and audit** obligations from licenses are tracked and enforceable;
  lineage (docs 05/07) is also the evidence trail for license compliance. **License-specific
  display obligations** — exchange attribution strings, delayed-data labeling ("data delayed
  15 min"), per-venue notice requirements — are captured per source in adapter metadata
  (doc 06) and injected by the entitlements engine at serve time, not hand-placed in UI
  (v2.0 tightening).
- **Mechanization lives in doc 17 (v2.0, per review B9):** this document *rules* on what
  license terms mean; the **entitlements engine (doc 17)** is the single enforcement
  abstraction — tier × license × field × delay — applied at the API edge and AI layer. No
  scattered per-endpoint license flags.

### Regulatory posture (retail financial content)
- **The no-advice boundary is architectural** (docs 01/09): the platform delivers explainable,
  *quantitative, general* analytics — not personalized investment advice. AI and API surfaces
  are constrained from issuing individualized buy/sell/hold recommendations. Jurisdictional
  advice-regulation applicability (e.g. investment-adviser rules) is a **must-be-decided with
  counsel** item before any feature approaches personalization.
- **Disclosures are systematic**, not decorative — provenance, methodology (doc 08 catalog),
  data freshness/quality, AI-generated-content labeling, and "not investment advice" are
  surfaced consistently through the API/frontend.
- **User-data & privacy regulation — named regimes (v2.0, per review B2):** the **India
  Digital Personal Data Protection Act, 2023** is the primary regime (the core user is the
  Indian retail investor): consent, purpose limitation, erasure rights, breach notification,
  and a **data-localization stance to be confirmed with counsel** (a named counsel-gate item).
  **GDPR** applies to any EU users. The lifecycle model that makes erasure and retention
  actually executable against immutable stores is doc 17; key mechanics are doc 13. v1.0's
  unreconciled "append-only forever vs. erasure rights" contradiction is resolved by that
  pair. Data minimization and consent are designed in.
- **Records & auditability** — the platform can reconstruct what it showed, from what data,
  under which methodology version, at a given time (bitemporal + lineage) — supporting both
  compliance inquiries and user complaints.

### Architectural switches this document requires to exist
1. The **entitlements engine (doc 17)** — tier × license × field × delay, enforced at the API
   edge (doc 10) and AI layer (doc 09), with license terms as adapter metadata (doc 06).
2. A **no-advice guardrail** in the AI layer (doc 09) and API.
3. **Systematic disclosure & AI-content labeling** in every derived/AI response — labeling is a
   compliance artifact backed by doc 09's residual-risk register (v2.0: because AI grounding is
   defense-in-depth, not a guarantee, honest labeling is the compliance posture).
4. **Lineage as compliance evidence** (docs 05/07) at the declared guarantee tier — audited
   surfaces are **bit-reproducible** (principle 6): the platform can reconstruct exactly what
   it showed, from what data, under which methodology and policy versions.
5. The **data-lifecycle model (doc 17)** — retention classes + lawful erasure.

## What must NOT live here
- Technical *implementation* of the switches — docs 05/06/09/10/13 (this doc mandates them).
- Security mechanics — doc 13.
- Final legal determinations — those require counsel; this doc marks the gates.

## Dependencies
- [01](01-vision.md) (non-goals: not advice), [05](05-market-data-architecture.md)/[06](06-provider-abstraction-layer.md)
  (license metadata + enforcement), [09](09-ai-framework.md)/[10](10-api-design.md)/[13](13-security.md) (enforcement points).

## Completion criteria
- [ ] Each provider's store/cache/redistribute/retain/attribution terms are captured as
      adapter metadata consumable by the doc 17 entitlements engine.
- [ ] The architecture can serve derived-only for any source that forbids redistribution.
- [ ] DPDP 2023 and GDPR obligations map to the doc 17 lifecycle + doc 13 mechanics;
      the localization question is a named counsel gate.
- [ ] The no-advice boundary and systematic disclosure/AI-labeling are specified as enforceable.
- [ ] "Commercial-grade licensed feed required before commercial launch" is an explicit roadmap gate.
- [ ] The list of "must be decided with counsel" items is written and owned before dependent phases ship.
