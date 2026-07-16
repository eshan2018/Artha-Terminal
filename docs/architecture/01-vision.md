# 01 · Vision

| | |
|---|---|
| **Status** | ✅ Approved — v2.0 baseline (2026-07-17) |
| **Version** | 2.0 (unchanged in substance by the v1.0 review — vision survived) |
| **Owner** | FinTech CTO |
| **Depends on** | — (root document) |
| **Consumed by** | All documents |

## Purpose
Fix, in writing, *what Nivesh Terminal is*, *who it serves*, and — most importantly — *what
it is deliberately not*, so that every downstream architectural decision has a stable target
to optimize for.

## Why it exists
Architecture is the art of saying no. Without an agreed vision, every technical decision
becomes re-litigated against an imagined product, and the platform accretes the union of all
possible products (screener + chatbot + robo-advisor + brokerage). This document is the veto
authority that keeps the system coherent.

## Decisions this document owns
- **What the product is.** A modular *financial research and intelligence terminal* for
  retail investors: aggregated market/fundamental/economic data, explainable analytics,
  AI-assisted research, and research workspaces — unified by traceability to source.
- **Who it serves.** Self-directed retail investors and enthusiasts who want
  institution-grade *research tooling* they can trust and interrogate, not a black box.
- **The differentiator: explainability + lineage.** Every number a user sees can be traced
  to its source data and the formula that produced it. This is the product moat and the
  reason the layered architecture is non-negotiable.
- **The product pillars** (each becomes one or more analytics/AI modules, never the core):
  fundamentals, market data, economic data, portfolio analytics, screening, valuation,
  earnings analysis, risk analytics, backtesting, AI-assisted research, research workspaces.
- **Success definition.** A retail user can answer a real research question ("is this company
  cheap given its risk?") end-to-end, and audit every input behind the answer.

## Non-goals (explicit)
- **Not a stock screener.** Screening is one query surface over the data platform.
- **Not an AI chatbot.** AI is a layer that consumes analytics; conversation is one interface.
- **Not a scoring engine.** Scoring is one analytics module among many; the platform does not
  reduce to a score.
- **Not a brokerage / execution venue.** No order routing, custody, or settlement.
- **Not a personalized advice service.** The platform delivers *explainable analytics*, not
  personalized investment recommendations. See doc 14.
- **Not real-time HFT infrastructure.** Latency target is "research-grade" (seconds–minutes),
  not microseconds. This choice cascades into every storage and provider decision.

## What must NOT live here
- Any technology choice (languages, databases, cloud). Those belong to docs 03/07/12.
- Feature specifications or UI copy. This is direction, not a product backlog.
- Timelines. Sequencing lives in doc 15.

## Dependencies
None. This is the root. Every other document must be checkable against it: "does this serve
the retail-research-terminal vision, or a product we said we are not building?"

## Completion criteria
- [ ] The product-is / product-is-not lists are agreed and unambiguous.
- [ ] The eleven pillars are each classifiable as "module," never "core."
- [ ] The explainability-and-lineage differentiator is accepted as an architectural
      constraint, not merely a feature.
- [ ] Every downstream document can cite this vision to justify a scope boundary.
