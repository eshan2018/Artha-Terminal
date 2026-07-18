# Implementation · 02 · Methodology Catalog

| | |
|---|---|
| **Status** | Living — implementation tier (established in M1; populated from M3) |
| **Owner** | Quantitative Systems Architect / implementing engineer |
| **Governed by** | Architecture v2.0 — [doc 08 Analytics Framework](../architecture/08-analytics-framework.md) |

## Purpose
The versioned, user-facing home for **every feature definition and analytics formula** the
platform ships — definition, assumptions, references, known limitations, and `formula_version`.
Doc 08 requires this catalog to exist; it is a compliance artifact (doc 14 — "quantitative,
not advice") and the raw material for the explainability "why?" panel.

## Rules (from doc 08 / doc 11)
1. **Every feature and formula has an entry** with a `version`. Changing a formula is a **new
   version**, never a silent edit.
2. **Golden-master provenance ([doc 11](../architecture/11-testing-strategy.md), B10):** a formula's first golden test is seeded
   **only after** it passes property-based tests and parity with an independent reference
   implementation. A golden must never enshrine a first-write bug.
3. **Determinism:** entries state any seed/parameters so results are reproducible ([doc 08](../architecture/08-analytics-framework.md)).
4. **Limitations are mandatory**, not optional — the honest boundary of each metric.

## Entry template
```markdown
### <feature-or-formula-id> · v<N>
- **Kind:** feature (L6) | engine formula (L7)
- **Definition:** the precise computation, in words + notation.
- **Inputs:** canonical entities / features consumed (with units).
- **Output:** value + unit/currency (or ratio); AnalyticResult envelope fields populated.
- **Assumptions:** what must hold for the result to be meaningful.
- **Limitations:** where it misleads; what it is NOT.
- **References:** sources for the method.
- **Determinism:** seeds/params, if any.
- **Tests:** reference values, property tests, reference-impl parity (doc 11).
```

## Catalog
_Empty in M1 — no feature or formula code exists yet (Phase 0)._ The first entry, **1-year
total return**, is authored in **Milestone M3** (doc 00, Part B) when the feature and engine
are built.

## Change log
| Date | Change |
|------|--------|
| 2026-07-17 | Catalog established (M1, Phase 0 convention). No entries yet; first entry lands in M3. |
