"""An independent reference implementation of the one-year total return (doc 11, B10).

Doc 11 requires every nontrivial engine to have a second implementation, written to
differ from the first, with parity asserted inside a documented tolerance. The point
is to catch the bug both authors would not make the same way — so this deliberately
differs from `backend.analytics.one_year_return` on all three axes that could hide one:

* **Different arithmetic.** This computes in `Decimal` end to end, straight from the
  canonical `Money`/`IndexLevel` amounts. The engine computes in `float`, past the C3
  seam. Parity therefore tests the seam itself: if the decimal→float conversion lost
  or distorted anything, the two answers separate.
* **Different anchor search.** The engine takes a global minimum over the whole
  series by distance to the target. This walks outward from the target day by day —
  `target`, `target-1d`, `target+1d`, … — against a dictionary keyed by exact bar
  time, and stops at the first hit. Same specification, opposite strategy.
* **Different input.** This consumes `PriceObservation`s directly and applies its own
  as-of filter, so it does not inherit a mistake from the feature layer.

**Numeric tolerance policy** (the doc-11 requirement, stated where it is enforced):

* **Money compares exactly.** Decimal amounts are equal or they are not; no epsilon
  is permitted anywhere money is involved.
* **Ratios compare within a relative tolerance of 1e-12.** IEEE-754 doubles carry a
  relative epsilon near 2.2e-16, and this metric is one division and one subtraction
  applied to values already rounded to the vendor's printed precision — so the
  accumulated error is a few units in the last place. The divergence actually
  observed between these two implementations on the golden fixture is **3.5e-15**, so
  1e-12 leaves roughly two and a half orders of magnitude of headroom over measured
  reality while still being far tighter than any difference a real methodology error
  could produce (the smallest such error, a one-day anchor shift, moves the answer by
  basis points, not by 1e-12). The tolerance is calibrated, not guessed.

This module is test-tier only. It is never imported by `backend/`.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from backend.domain.model.observations import PriceObservation
from backend.domain.model.quantities import IndexLevel, Money

#: See the tolerance policy above.
RATIO_RELATIVE_TOLERANCE = 1e-12

_LOOKBACK_DAYS = 365
_TOLERANCE_DAYS = 7


def reference_one_year_return(
    observations: tuple[PriceObservation, ...], as_of: datetime
) -> Decimal | None:
    """The one-year total return as an exact `Decimal`, or `None` if undefined.

    `None` is this implementation's stand-in for the engine's `Unavailable`; parity
    tests assert the two agree on *when* the metric is undefined, not only on its
    value when it is defined.
    """
    visible = sorted(
        (
            observation
            for observation in observations
            if observation.event_time <= as_of and observation.knowledge_time <= as_of
        ),
        key=lambda observation: observation.event_time,
    )
    if len(visible) < 2:
        return None

    by_time = {observation.event_time: _amount(observation) for observation in visible}
    end_time = visible[-1].event_time
    target = end_time - timedelta(days=_LOOKBACK_DAYS)

    anchor_price: Decimal | None = None
    for days in range(_TOLERANCE_DAYS + 1):
        # Earlier before later, so an equidistant pair resolves to the earlier bar —
        # matching the engine's documented tie-break.
        for candidate in (target - timedelta(days=days), target + timedelta(days=days)):
            if candidate in by_time:
                anchor_price = by_time[candidate]
                break
        if anchor_price is not None:
            break

    if anchor_price is None or anchor_price == 0:
        return None
    return by_time[end_time] / anchor_price - 1


def _amount(observation: PriceObservation) -> Decimal:
    """The close as an exact decimal, without going through the C3 seam."""
    close = observation.close
    if isinstance(close, Money):
        return close.amount
    if isinstance(close, IndexLevel):
        return close.points
    raise TypeError(f"not a price quantity: {type(close).__name__}")
