"""Tests for the validation gate (L3, doc 05).

The gate's core promise is fail-closed and lossless-at-the-boundary: every input
bar lands in exactly one of `accepted` or `quarantined`, bad data never proceeds,
and nothing is silently repaired.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.domain.model.instruments import reference_for
from backend.ingestion.validation import (
    FLAG_STALE_SERIES,
    FLAG_UNEXPLAINED_JUMP,
    validate_price_history,
)
from backend.platform.identifiers import InstrumentId
from backend.providers.ports.price_history import (
    FetchMetadata,
    RawBar,
    RawPriceResponse,
)

APPLE = reference_for(InstrumentId("apple"))
NIFTY = reference_for(InstrumentId("nifty-50"))


def _response(bars: tuple[RawBar, ...], instrument: str = "apple") -> RawPriceResponse:
    return RawPriceResponse(
        instrument_id=InstrumentId(instrument),
        bars=bars,
        fetch=FetchMetadata(
            provider="yfinance",
            vendor_symbol="AAPL",
            interval="1d",
            fetched_at=datetime(2025, 7, 15, tzinfo=UTC),
            raw_contract_version="yfinance-ohlcv/v1",
        ),
    )


def _bar(day: int, close: float = 100.0, **overrides: object) -> RawBar:
    values: dict[str, object] = {
        "timestamp": f"2025-07-{day:02d}T00:00:00",
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": close,
        "volume": 1000.0,
    }
    values.update(overrides)
    return RawBar(**values)  # type: ignore[arg-type]


def test_clean_payload_is_fully_accepted() -> None:
    outcome = validate_price_history(_response((_bar(1), _bar(2, close=101.0))), APPLE)
    assert len(outcome.accepted) == 2
    assert outcome.quarantined == ()
    assert outcome.series_flags == ()


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"close": -5.0}, "close must be > 0"),
        ({"close": 0.0}, "close must be > 0"),
        ({"volume": -1.0}, "volume must be non-negative"),
        ({"close": None}, "missing required field"),
        ({"high": 50.0}, "high"),  # high below low/open/close
        ({"low": 150.0}, "low"),  # low above open/close
        ({"timestamp": "not-a-date"}, "unparseable timestamp"),
    ],
)
def test_hard_failures_are_quarantined_with_reasons(
    overrides: dict[str, object], expected: str
) -> None:
    outcome = validate_price_history(_response((_bar(1, **overrides),)), APPLE)
    assert outcome.accepted == ()
    assert len(outcome.quarantined) == 1
    assert any(expected in reason for reason in outcome.quarantined[0].reasons)


def test_duplicate_bars_are_quarantined_not_deduplicated() -> None:
    outcome = validate_price_history(_response((_bar(1), _bar(1))), APPLE)
    assert len(outcome.accepted) == 1
    assert len(outcome.quarantined) == 1
    assert any("duplicate" in r for r in outcome.quarantined[0].reasons)


def test_every_input_bar_is_accounted_for() -> None:
    bars = (_bar(1), _bar(2, close=-1.0), _bar(3), _bar(4, close=None))
    outcome = validate_price_history(_response(bars), APPLE)
    assert len(outcome.accepted) + len(outcome.quarantined) == len(bars)


def test_stale_series_raises_a_soft_flag_without_rejecting() -> None:
    outcome = validate_price_history(
        _response((_bar(1, close=100.0), _bar(2, close=100.0))), APPLE
    )
    assert len(outcome.accepted) == 2  # not rejected
    assert outcome.series_flags == (FLAG_STALE_SERIES,)


def test_unexplained_jump_is_flagged_not_dropped() -> None:
    outcome = validate_price_history(
        _response((_bar(1, close=100.0), _bar(2, close=400.0, high=500.0))), APPLE
    )
    assert len(outcome.accepted) == 2
    flags = [f for bar in outcome.accepted for f in bar.quality_flags]
    assert FLAG_UNEXPLAINED_JUMP in flags


def test_index_instrument_validates_without_currency() -> None:
    outcome = validate_price_history(_response((_bar(1),), instrument="nifty-50"), NIFTY)
    assert len(outcome.accepted) == 1
