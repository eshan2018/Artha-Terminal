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

### close_price_series · v1
- **Kind:** feature (L6) — `backend/features/returns.py`
- **Version string:** `close-price-series/v1`
- **Definition:** For an instrument, an interval, and a knowledge cutoff `as_of`, the ordered
  sequence of `(event_time, close)` pairs drawn from the canonical `PriceObservation`s that were
  known at `as_of`. An observation is admitted only if **both** `event_time ≤ as_of` **and**
  `knowledge_time ≤ as_of`. Points are ordered by `event_time`, ascending.
- **Inputs:** `PriceObservation.close` — `Money(Decimal, currency)` for equities,
  `IndexLevel(Decimal)` (unitless points) for indices — read through `MarketDataRepository`.
- **Output:** `ClosePriceSeries`; each `PricePoint.price` is a `float`. The lineage
  `FeatureRef` pins the feature version, every observation consumed, **and the parameters the
  feature was called with** (`interval`), so the invocation is reproducible and a daily series is
  distinguishable from a weekly one.
- **Unknown instrument:** raises `UnknownInstrument` rather than returning an empty series. A
  mistyped identifier and a known instrument with no data are different answers to "why is this
  blank?", and only the second is an `Unavailable`.
- **The C3 seam:** this feature performs the platform's **single, one-way decimal→float
  conversion**, in `returns.to_float`. Money is exact `Decimal` at rest, in the domain and at the
  API; it becomes `float` here, once, for statistical consumption. There is deliberately no
  inverse — converting a statistical float back into money is forbidden (doc 04 / ADR-0016).
- **Assumptions:**
  1. `close` is the **adjusted** close. The provider is fetched with `auto_adjust=True`
     (`backend/providers/yfinance/adapter.py`), so splits and dividends are already reflected in
     the series by the vendor.
  2. All observations for an instrument share a reference-data snapshot version.
- **Limitations:**
  1. **Adjustment is inherited, not verified.** The platform does not compute its own corporate
     -action adjustment — `CorporateAction` is not an ingested data class in the skeleton — so
     the series trusts the vendor's adjustment. A provider change, or `auto_adjust=False`, would
     silently change the meaning of `close` without changing this feature's version. The
     canonical model also has no distinct `adjusted_close` field to make the distinction
     explicit; adding one is Phase 1 model-hardening work.
  2. **The as-of filter sits above a latest-version read.** The repository returns the latest
     version of each bar (as-of query machinery is deferred to Phase 6, doc 04). If a bar was
     later corrected and that correction's `knowledge_time` is after `as_of`, the bar is dropped
     rather than falling back to the version known at the time. That is fail-closed — absence
     rather than a value we could not have seen — but narrower than a true as-of read.
  3. Mixed reference-snapshot versions across observations are flagged
     (`reference-version-drift`), not reconciled.
- **Determinism:** pure given `(repository contents, instrument_id, interval, as_of)`. No clock,
  no randomness. `as_of` is an explicit input (principle 11).
- **Tests:** `backend/tests/features/test_returns.py` — seam conversion in both price types and
  the absence of an inverse; the lookahead filter on both time axes; lineage completeness and
  the exclusion of filtered-out observations; version pinning; drift flagging.

### one-year-total-return · v1
- **Kind:** engine formula (L7) — `backend/analytics/one_year_return.py`
- **Version string:** `one-year-total-return/v1`
- **Definition:** Let `S` be a `close_price_series` evaluated at `as_of`, with at least two
  points. Let `P_end` be the last point and `t_end` its `event_time`. Let the target be
  `t_target = t_end − 365 calendar days`, and let `P_start` be the point of `S` whose
  `event_time` is nearest `t_target`, ties resolving to the **earlier** bar. If
  `|event_time(P_start) − t_target| > 7 days`, the metric is `Unavailable`. Otherwise:

  > **one_year_return = (P_end / P_start) − 1**

  The result is a unitless `Ratio`, unrounded.
- **Inputs:** the `close_price_series` feature (L6). **No repository access** — engines consume
  features and other engines' results only (doc 08 / ADR-0014), enforced by the CI dependency
  lint.
- **Output:** `AnalyticResult` with `value: Ratio`, `formula_version`, `reference_version`,
  `as_of`, `computed_at`, `quality_flags`, and a `LineageHandle` resolving to the feature
  version → the observations consumed → their raw object keys, provider and contract version.
- **Assumptions:**
  1. A **365-calendar-day** window, not a 252-trading-day one, so the window means the same
     thing across exchanges with different holiday calendars.
  2. The nearest bar within **7 calendar days** of the target is an acceptable anchor. Seven
     days spans the longest ordinary closure on the exchanges in scope, and accommodates weekly
     bars (worst-case distance 3.5 days).
  3. Prices are adjusted (inherited from the feature's assumption 1), so the figure is a **total**
     return including dividends, not a price return.
  4. The series is denominated in a single currency throughout the window.
- **Limitations:**
  1. **It is a point-to-point return, not an annualized or risk-adjusted one.** It says nothing
     about the path, the drawdown, or the volatility between the two dates.
  2. **The anchor is approximate whenever the target date has no bar.** The actual offset is
     published as a `anchor-offset-days:N` quality flag; a non-zero offset means a window
     slightly longer or shorter than a year was measured. Ignoring that flag overstates precision.
  3. **No currency conversion is applied or needed** — a ratio is FX-invariant — but comparing
     this metric across instruments in different currencies compares *local* returns, which is
     not the same as an investor's realized return after FX.
  4. **Vendor-adjusted inputs** (feature limitation 1) mean an adjustment error at the provider
     propagates here undetected.
  5. **Not advice.** A quantitative measure of past price change; it has no predictive claim
     (doc 14).
- **Unavailable reasons** (a missing input is never zero — principle 13). The reason is shown to
  the user in place of the number, so each names a distinct, actionable condition:
  | Reason | Condition |
  |---|---|
  | `no-observations-available-at-as-of` | The series is empty at the knowledge cutoff. |
  | `insufficient-history-for-a-one-year-window` | Fewer than two points, **or** the earliest bar is later than `t_target + 7 days` — the history does not reach back a year. The common case for a newly listed instrument or a short backfill. |
  | `no-observation-within-tolerance-of-the-one-year-anchor` | The history *does* reach back far enough, but there is a gap where the anchor belongs. |
  | `anchor-price-is-zero-so-the-return-is-undefined` | Division by zero (the prototype's `safe_div` discipline). |
- **References:** the prototype's `shared/calculations.py::get_return` is the **reference for the
  shape** of this calculation, ported behind the engine contract rather than lifted (ADR-0014).
  Three deliberate differences: the anchor tolerance is tightened from 45 days to 7 (a 45-day
  error on the anchor is a materially different metric); the result is an unrounded ratio rather
  than a percentage rounded to 2dp, because rounding is presentation and belongs at the API edge;
  and the answer arrives in a traced envelope instead of as a bare float.
- **Determinism:** pure. No I/O, no clock, no randomness, therefore no seed. `as_of` arrives on
  the feature and `computed_at` is an explicit argument. Same inputs + same versions ⇒
  bit-identical output.
- **Tests:** `backend/tests/analytics/`
  - *Reference values:* ±20% over an exact year; the unitless-ness of an index vs an equity; an
    off-target anchor and its flag.
  - *Property-based* (hypothesis, `derandomize=True`): a flat series returns exactly zero;
    **currency-scale invariance** (the property guarding the C3 seam); the return is bounded
    below by −1; raising the final price raises the return; determinism.
  - *Independent reference implementation:* `reference_implementation.py` — `Decimal` arithmetic
    straight from the canonical amounts (bypassing the seam) and an outward day-by-day anchor
    search against a time-keyed map, rather than the engine's float arithmetic and global
    minimum-distance scan. Parity asserted on value **and on availability**.
  - *Numeric tolerance policy:* **money compares exactly**; **ratios within a relative 1e-12**.
    Observed divergence between the two implementations on the golden fixture is **3.5e-15**, so
    the tolerance carries ~2.5 orders of magnitude of headroom over measured reality while
    remaining far tighter than any real methodology error (a one-day anchor shift moves the
    answer by basis points).

#### Golden-master seeding record (doc 11 B10 — governed provenance)
| | |
|---|---|
| **Golden** | `backend/tests/analytics/golden/one_year_return_v1.json` |
| **Seeded** | 2026-07-18, during M3 |
| **Procedure** | 1. Property tests and reference-implementation parity written and run **first**. 2. Suite green (27 tests) with **no golden present**. 3. Engine output on the fixed 400-bar fixture cross-checked against the independent reference implementation: relative difference **3.5e-15**, inside the 1e-12 policy. 4. Only then was the golden written, from the code that had passed. |
| **Guards** | Unintended methodology drift — the anchor rule, tolerance, tie-break, and envelope shape. Not correctness; the tests above own that. |
| **Change rule** | Changing the golden requires a `formula_version` bump and review. Editing the values to match new output without one is the failure mode B10 exists to prevent. |

## Change log
| Date | Change |
|------|--------|
| 2026-07-17 | Catalog established (M1, Phase 0 convention). No entries yet; first entry lands in M3. |
| 2026-07-18 | **First entries authored (M3):** `close_price_series · v1` (L6, the C3 seam) and `one-year-total-return · v1` (L7). Golden-master seeding record added after property + parity tests passed. |
