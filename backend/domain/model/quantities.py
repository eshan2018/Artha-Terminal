"""Canonical quantity value types (doc 04, ADR-0016).

Two rules are enforced *structurally*, not by convention:

* **Money is never a float.** `Money.amount` must be a `Decimal`; passing a float
  raises. Binary floating point cannot represent money exactly, so the type makes
  float-money unrepresentable rather than merely discouraged.
* **Index levels are unitless points and cannot be FX-converted.** `IndexLevel`
  has no currency field at all, so there is no currency to convert — the prototype's
  index-inflation bug is type-impossible here, exactly as doc 04 requires.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Currency(StrEnum):
    """Currencies the skeleton handles. Extended as markets are added."""

    INR = "INR"
    USD = "USD"


def to_decimal(value: float | int | str | Decimal) -> Decimal:
    """Convert a raw provider numeric into an exact `Decimal`.

    This is the sanctioned raw→canonical numeric boundary (L4). Floats are routed
    through `str()` so the decimal matches the vendor's printed representation
    rather than the binary-float artifact (`Decimal(0.1)` would be
    `0.1000000000000000055511151231257827`).

    Note this is *not* the C3 decimal→float seam: that seam is money→float at
    feature-layer ingress (L6) for statistics, and converting those statistical
    floats back into money is forbidden.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):  # bool is an int subclass; never a quantity
        raise TypeError("bool is not a valid quantity value")
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class Money:
    """An exact monetary amount in an explicit currency."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, Decimal):
            raise TypeError(
                f"Money.amount must be a Decimal, got {type(self.amount).__name__} "
                "(money is never a float — ADR-0016)"
            )
        if not isinstance(self.currency, Currency):
            raise TypeError("Money.currency must be a Currency")


@dataclass(frozen=True, slots=True)
class Ratio:
    """A unitless statistical quantity — a return, a volatility, a Sharpe ratio.

    Deliberately a `float`, and deliberately *not* money. ADR-0016 permits binary
    floating point for statistical quantities precisely because they are not
    monetary: a ratio has no currency to be exact in. The type exists so a bare
    number never crosses a layer boundary (doc 04) and so that a ratio can never be
    mistaken for — or converted back into — money, which C3 forbids.
    """

    value: float

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, float):
            raise TypeError(
                f"Ratio.value must be a float, got {type(self.value).__name__} "
                "(ratios are statistical quantities, not money — ADR-0016)"
            )


@dataclass(frozen=True, slots=True)
class IndexLevel:
    """An index level in unitless points. Deliberately carries no currency."""

    points: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.points, bool) or not isinstance(self.points, Decimal):
            raise TypeError(
                f"IndexLevel.points must be a Decimal, got {type(self.points).__name__}"
            )


# The value a price can take. An index price can never be treated as money.
PriceValue = Money | IndexLevel
