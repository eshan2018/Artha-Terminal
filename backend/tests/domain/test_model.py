"""Tests for the canonical model's structural guarantees (doc 04, ADR-0016)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from backend.domain.model.instruments import (
    REFERENCE_VERSION,
    InstrumentReference,
    InstrumentType,
    UnknownInstrument,
    known_instruments,
    reference_for,
)
from backend.domain.model.quantities import Currency, IndexLevel, Money, to_decimal
from backend.platform.identifiers import InstrumentId

# ── Money is never a float ────────────────────────────────────────────────────

def test_money_requires_decimal_and_rejects_float() -> None:
    assert Money(Decimal("100.50"), Currency.INR).amount == Decimal("100.50")
    with pytest.raises(TypeError):
        Money(100.50, Currency.INR)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        IndexLevel(24_500.75)  # type: ignore[arg-type]


def test_to_decimal_avoids_binary_float_artifacts() -> None:
    # Decimal(0.1) would be 0.1000000000000000055511151231257827
    assert to_decimal(0.1) == Decimal("0.1")
    assert to_decimal("100.50") == Decimal("100.50")
    assert to_decimal(Decimal("7")) == Decimal("7")
    with pytest.raises(TypeError):
        to_decimal(True)  # bool is not a quantity


# ── An index can never be FX-converted ────────────────────────────────────────

def test_index_level_has_no_currency_field() -> None:
    level = IndexLevel(Decimal("24500.75"))
    assert not hasattr(level, "currency")


def test_index_reference_may_not_carry_a_currency() -> None:
    with pytest.raises(ValueError, match="INDEX"):
        InstrumentReference(
            InstrumentId("bad-index"), "Bad", InstrumentType.INDEX, Currency.INR
        )


def test_equity_reference_requires_a_currency() -> None:
    with pytest.raises(ValueError, match="EQUITY"):
        InstrumentReference(InstrumentId("bad-equity"), "Bad", InstrumentType.EQUITY, None)


# ── Provisional reference state ───────────────────────────────────────────────

def test_registry_covers_the_five_skeleton_instruments() -> None:
    refs = {r.instrument_id.value: r for r in known_instruments()}
    assert set(refs) == {"reliance", "tcs", "infosys", "nifty-50", "apple"}
    assert refs["nifty-50"].type is InstrumentType.INDEX
    assert refs["nifty-50"].currency is None
    assert refs["apple"].currency is Currency.USD
    assert refs["reliance"].currency is Currency.INR


def test_reference_version_is_pinned() -> None:
    assert REFERENCE_VERSION == "skeleton-reference/v1"


def test_unknown_instrument_raises() -> None:
    with pytest.raises(UnknownInstrument):
        reference_for(InstrumentId("not-a-thing"))
