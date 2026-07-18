"""Tests for normalization (L4) — canonical, exact, traceable observations."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from backend.domain.model.instruments import REFERENCE_VERSION, reference_for
from backend.domain.model.observations import AuthorityTier
from backend.domain.model.quantities import Currency, IndexLevel, Money
from backend.ingestion.normalization import normalize_price_history
from backend.ingestion.validation import validate_price_history
from backend.platform.identifiers import InstrumentId
from backend.providers.ports.price_history import (
    FetchMetadata,
    RawBar,
    RawPriceResponse,
)

KNOWLEDGE_TIME = datetime(2025, 7, 15, 9, 30, tzinfo=UTC)
RAW_KEY = "raw/v1/yfinance/price-history/2025-07/apple/abc.json"


def _response(instrument: str, bars: tuple[RawBar, ...]) -> RawPriceResponse:
    return RawPriceResponse(
        instrument_id=InstrumentId(instrument),
        bars=bars,
        fetch=FetchMetadata(
            provider="yfinance",
            vendor_symbol="AAPL",
            interval="1d",
            fetched_at=KNOWLEDGE_TIME,
            raw_contract_version="yfinance-ohlcv/v1",
        ),
    )


def _bar(day: int, close: float = 100.5, **overrides: object) -> RawBar:
    """A well-formed bar. high/low are derived from open/close so that varying
    `close` keeps the bar internally consistent (the gate rejects inconsistent OHLC).
    """
    open_ = 100.0
    values: dict[str, object] = {
        "timestamp": f"2025-07-{day:02d}T00:00:00",
        "open": open_,
        "high": max(open_, close) * 1.05,
        "low": min(open_, close) * 0.95,
        "close": close,
        "volume": 1000.0,
    }
    values.update(overrides)
    return RawBar(**values)  # type: ignore[arg-type]


def _normalize(instrument: str, bars: tuple[RawBar, ...]):
    reference = reference_for(InstrumentId(instrument))
    response = _response(instrument, bars)
    outcome = validate_price_history(response, reference)
    return normalize_price_history(
        response,
        outcome,
        reference,
        knowledge_time=KNOWLEDGE_TIME,
        raw_object_key=RAW_KEY,
        reference_version=REFERENCE_VERSION,
    )


# ── Money and units ───────────────────────────────────────────────────────────

def test_equity_prices_are_decimal_money_in_native_currency() -> None:
    (observation,) = _normalize("apple", (_bar(1, close=100.5),))
    assert isinstance(observation.close, Money)
    assert observation.close.amount == Decimal("100.5")
    assert observation.close.currency is Currency.USD  # preserved, not converted


def test_inr_equity_keeps_inr() -> None:
    (observation,) = _normalize("reliance", (_bar(1),))
    assert isinstance(observation.close, Money)
    assert observation.close.currency is Currency.INR


def test_index_prices_are_unitless_points_and_cannot_be_fx_converted() -> None:
    (observation,) = _normalize("nifty-50", (_bar(1, close=24500.75),))
    assert isinstance(observation.close, IndexLevel)
    assert observation.close.points == Decimal("24500.75")
    assert not hasattr(observation.close, "currency")


def test_money_is_exact_not_binary_float() -> None:
    (observation,) = _normalize("apple", (_bar(1, close=0.1),))
    assert isinstance(observation.close, Money)
    assert observation.close.amount == Decimal("0.1")
    assert str(observation.close.amount) == "0.1"


# ── Time (C1) ─────────────────────────────────────────────────────────────────

def test_knowledge_time_is_populated_on_every_observation() -> None:
    observations = _normalize("apple", (_bar(1), _bar(2)))
    assert len(observations) == 2
    assert all(o.knowledge_time == KNOWLEDGE_TIME for o in observations)
    assert all(o.knowledge_time.tzinfo is not None for o in observations)


def test_event_time_is_parsed_and_ordered() -> None:
    observations = _normalize("apple", (_bar(3), _bar(1), _bar(2)))
    assert [o.event_time.day for o in observations] == [1, 2, 3]


def test_knowledge_time_must_be_timezone_aware() -> None:
    reference = reference_for(InstrumentId("apple"))
    response = _response("apple", (_bar(1),))
    outcome = validate_price_history(response, reference)
    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_price_history(
            response,
            outcome,
            reference,
            knowledge_time=datetime(2025, 7, 15, 9, 30),  # naive
            raw_object_key=RAW_KEY,
            reference_version=REFERENCE_VERSION,
        )


# ── Provenance, authority, fail-closed ────────────────────────────────────────

def test_provenance_pins_raw_object_and_versions() -> None:
    (observation,) = _normalize("apple", (_bar(1),))
    provenance = observation.provenance
    assert provenance.raw_object_key == RAW_KEY
    assert provenance.provider == "yfinance"
    assert provenance.raw_contract_version == "yfinance-ohlcv/v1"
    assert provenance.reference_version == REFERENCE_VERSION


def test_provider_data_is_stamped_authoritative() -> None:
    (observation,) = _normalize("apple", (_bar(1),))
    assert observation.authority is AuthorityTier.AUTHORITATIVE


def test_quarantined_bars_never_reach_the_canonical_model() -> None:
    observations = _normalize("apple", (_bar(1), _bar(2, close=-5.0), _bar(3)))
    assert len(observations) == 2  # the bad bar is absent, not zero-filled
    assert all(o.close.amount > 0 for o in observations)  # type: ignore[union-attr]


def test_quality_flags_travel_with_the_observation() -> None:
    observations = _normalize("apple", (_bar(1, close=100.0), _bar(2, close=100.0)))
    assert all("stale-series" in o.quality_flags for o in observations)
