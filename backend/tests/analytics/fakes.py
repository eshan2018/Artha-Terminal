"""Test doubles shared by the L7 suites."""
from __future__ import annotations

from collections.abc import Sequence

from backend.domain.model.observations import PriceObservation, QuarantineRecord
from backend.platform.identifiers import InstrumentId


class FakeRepository:
    """An in-memory `MarketDataRepository`.

    Used in place of SQLite where a suite builds hundreds of series per run: the
    storage engine is not what those tests exercise (the repository's own contract has
    its own suite against the real backend), and the feature layer is still driven for
    real through the port.
    """

    def __init__(self, observations: Sequence[PriceObservation]) -> None:
        self._observations = tuple(observations)

    def save_observations(self, observations: Sequence[PriceObservation]) -> int:
        raise NotImplementedError

    def get_observations(
        self, instrument_id: InstrumentId, *, interval: str
    ) -> tuple[PriceObservation, ...]:
        return tuple(
            observation
            for observation in self._observations
            if observation.instrument_id == instrument_id and observation.interval == interval
        )

    def save_quarantined(self, records: Sequence[QuarantineRecord]) -> int:
        raise NotImplementedError

    def get_quarantined(self, instrument_id: InstrumentId) -> tuple[QuarantineRecord, ...]:
        return ()
