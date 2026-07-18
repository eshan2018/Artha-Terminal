"""Instrument reference data (doc 04).

`InstrumentType` is what makes units and valid analytics knowable — in particular
that index levels are unitless points and must never be FX-converted. The type and
currency invariant is enforced in the constructor, so an index carrying a currency
cannot be constructed at all.

**Provisional (Phase 0.5).** The registry below is a hand-held table for the
skeleton's five instruments, carrying an explicit `REFERENCE_VERSION` so any
computation can pin the reference state it used (doc 04 / review B1). Phase 1
replaces it with the effective-dated reference/master store; the *version* concept
survives that move unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.domain.model.quantities import Currency
from backend.platform.identifiers import InstrumentId

# The pinned version of this reference state (review B1 / lineage tiers).
REFERENCE_VERSION = "skeleton-reference/v1"


class InstrumentType(StrEnum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"


class UnknownInstrument(LookupError):
    """No reference data exists for the requested instrument."""


@dataclass(frozen=True, slots=True)
class InstrumentReference:
    """Canonical attributes of an instrument (vendor-neutral)."""

    instrument_id: InstrumentId
    name: str
    type: InstrumentType
    currency: Currency | None

    def __post_init__(self) -> None:
        if self.type is InstrumentType.EQUITY and self.currency is None:
            raise ValueError(f"{self.instrument_id} is an EQUITY and must have a currency")
        if self.type is InstrumentType.INDEX and self.currency is not None:
            raise ValueError(
                f"{self.instrument_id} is an INDEX: index levels are unitless points and "
                "must not carry a currency (doc 04 — FX conversion must be impossible)"
            )


_REGISTRY: dict[str, InstrumentReference] = {
    ref.instrument_id.value: ref
    for ref in (
        InstrumentReference(
            InstrumentId("reliance"), "Reliance Industries", InstrumentType.EQUITY, Currency.INR
        ),
        InstrumentReference(
            InstrumentId("tcs"), "Tata Consultancy Services", InstrumentType.EQUITY, Currency.INR
        ),
        InstrumentReference(
            InstrumentId("infosys"), "Infosys", InstrumentType.EQUITY, Currency.INR
        ),
        InstrumentReference(InstrumentId("nifty-50"), "Nifty 50", InstrumentType.INDEX, None),
        InstrumentReference(
            InstrumentId("apple"), "Apple Inc.", InstrumentType.EQUITY, Currency.USD
        ),
    )
}


def reference_for(instrument_id: InstrumentId) -> InstrumentReference:
    """Return reference data for `instrument_id`, or raise `UnknownInstrument`."""
    try:
        return _REGISTRY[instrument_id.value]
    except KeyError:
        raise UnknownInstrument(
            f"no reference data for instrument {instrument_id.value!r} "
            f"(reference {REFERENCE_VERSION})"
        ) from None


def known_instruments() -> tuple[InstrumentReference, ...]:
    """All instruments in the current (provisional) reference state."""
    return tuple(_REGISTRY.values())
