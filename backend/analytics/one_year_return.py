"""The `one_year_return` engine (L7, doc 08). Methodology: catalog entry
`one-year-total-return · v1`.

The skeleton's one metric, and the template every later engine follows:

* **Typed inputs, no repository.** The engine takes a `ClosePriceSeries` feature and
  explicit parameters. It cannot reach the domain store — the CI dependency lint
  forbids `backend.analytics` from importing `backend.domain.market_data` at all.
* **A pure, deterministic core.** No I/O, no clock, no randomness. `as_of` arrives on
  the feature and `computed_at` is an explicit argument, so the same inputs and
  versions always produce a bit-identical result (principle 11).
* **Versioned methodology.** `FORMULA_VERSION` is part of the answer. Changing the
  formula means a new version, never a silent edit, so old results stay reproducible.
* **Absence, never fabrication.** Every path that cannot produce a defensible number
  returns `Unavailable` with a specific reason. There is no branch that returns zero
  for missing data (principle 13) — and the envelope would reject one if there were.

**Ported, not lifted (ADR-0014).** The prototype's `shared/calculations.py::get_return`
is the reference for the shape of this calculation, not its source. Three deliberate
differences: the anchor tolerance is tightened from 45 days to 7 (a 45-day error on
the anchor date is a materially different metric); the result is an unrounded ratio
rather than a percentage rounded to two decimals, because rounding is a presentation
concern that belongs at the API edge; and the answer arrives in a traced envelope.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from backend.domain.model.analytics import AnalyticResult, LineageHandle
from backend.domain.model.quantities import Ratio
from backend.features.returns import ClosePriceSeries, PricePoint

METRIC_ID = "one_year_return"
FORMULA_VERSION = "one-year-total-return/v1"

#: The lookback, in calendar days. Calendar-based rather than a trading-day count so
#: the window means the same thing across exchanges with different holiday calendars.
LOOKBACK = timedelta(days=365)

#: How far the anchor bar may sit from the target date. Markets close for weekends and
#: holiday clusters, so the exact target date usually has no bar; 7 days spans the
#: longest ordinary closure on the exchanges in scope, and also accommodates weekly
#: bars (whose worst-case distance from any target is 3.5 days). Wider tolerances buy
#: availability by silently measuring a different window.
ANCHOR_TOLERANCE = timedelta(days=7)

# Unavailable reasons. Specific rather than generic: the reason is shown to the user
# in place of the number, so "why is this blank?" has to be answerable.
NO_OBSERVATIONS = "no-observations-available-at-as-of"
INSUFFICIENT_HISTORY = "insufficient-history-for-a-one-year-window"
NO_ANCHOR_IN_TOLERANCE = "no-observation-within-tolerance-of-the-one-year-anchor"
ZERO_ANCHOR_PRICE = "anchor-price-is-zero-so-the-return-is-undefined"

#: The anchor bar was not exactly 365 days before the latest bar. Emitted with the
#: actual offset in days, so the consumer can see how approximate the window is.
ANCHOR_OFFSET_FLAG = "anchor-offset-days"


def one_year_return(series: ClosePriceSeries, *, computed_at: datetime) -> AnalyticResult:
    """Compute the one-year total return for `series`.

    Returns `(P_end / P_start) - 1` as a unitless `Ratio`, where `P_end` is the latest
    close at or before the series' `as_of` and `P_start` is the close nearest to one
    year before `P_end`'s bar date, within `ANCHOR_TOLERANCE`.

    Being a ratio, the result is invariant to the currency the prices are quoted in —
    which is why this metric is safe to compute without any FX conversion, and why it
    was chosen as the skeleton's one metric.
    """
    if computed_at.tzinfo is None:
        raise ValueError("computed_at must be timezone-aware")

    lineage = LineageHandle(features=(series.lineage,))

    def unavailable(reason: str) -> AnalyticResult:
        return AnalyticResult.unavailable(
            metric_id=METRIC_ID,
            instrument_id=series.instrument_id,
            reason=reason,
            formula_version=FORMULA_VERSION,
            reference_version=series.reference_version,
            as_of=series.as_of,
            computed_at=computed_at,
            quality_flags=series.quality_flags,
            lineage=lineage,
        )

    if not series.points:
        return unavailable(NO_OBSERVATIONS)
    if len(series.points) < 2:
        return unavailable(INSUFFICIENT_HISTORY)

    end = series.points[-1]
    target = end.event_time - LOOKBACK

    # Distinguish "the series does not reach back a year" from "it does, but there is a
    # gap where the anchor should be". Both are Unavailable, but they are different
    # answers to the user's actual question, and the first is by far the common case
    # for a newly listed instrument or a short backfill.
    if series.points[0].event_time > target + ANCHOR_TOLERANCE:
        return unavailable(INSUFFICIENT_HISTORY)

    start = _anchor(series.points, target)
    if start is None:
        return unavailable(NO_ANCHOR_IN_TOLERANCE)
    if start.price == 0.0:
        return unavailable(ZERO_ANCHOR_PRICE)

    offset_days = round((start.event_time - target).total_seconds() / 86400)
    flags = set(series.quality_flags)
    if offset_days != 0:
        flags.add(f"{ANCHOR_OFFSET_FLAG}:{offset_days}")

    return AnalyticResult.available(
        metric_id=METRIC_ID,
        instrument_id=series.instrument_id,
        value=Ratio(end.price / start.price - 1.0),
        formula_version=FORMULA_VERSION,
        reference_version=series.reference_version,
        as_of=series.as_of,
        computed_at=computed_at,
        quality_flags=tuple(sorted(flags)),
        lineage=lineage,
    )


def _anchor(points: tuple[PricePoint, ...], target: datetime) -> PricePoint | None:
    """The point nearest `target`, or `None` if the nearest is outside tolerance.

    Ties break toward the earlier bar. The tie-break is arbitrary but must be *fixed*:
    an unspecified one would make the metric non-deterministic on evenly spaced data,
    which weekly bars produce routinely.
    """
    if not points:
        return None
    nearest = min(points, key=lambda p: (abs(p.event_time - target), p.event_time))
    return nearest if abs(nearest.event_time - target) <= ANCHOR_TOLERANCE else None
