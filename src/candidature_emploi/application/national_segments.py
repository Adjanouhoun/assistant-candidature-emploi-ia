"""Découpage contrôlé de la collecte nationale France Travail."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from candidature_emploi.domain.offers import Region

MAX_OFFERS_PER_SEGMENT = 3150
MIN_SEGMENT_DURATION = timedelta(seconds=1)


class SegmentCounter(Protocol):
    def count_region_segment(
        self,
        region_code: str,
        start: datetime,
        end: datetime,
    ) -> int: ...


@dataclass(frozen=True, slots=True)
class NationalSegment:
    region_code: str
    start: datetime
    end: datetime
    total: int


def plan_national_segments(
    counter: SegmentCounter,
    regions: list[Region],
    start: datetime,
    end: datetime | None = None,
) -> list[NationalSegment]:
    """Retourne des segments complets ou échoue avant toute suppression."""

    if start.tzinfo is None:
        raise ValueError("La date de début doit être exprimée avec un fuseau horaire.")
    end = end or datetime.now(UTC)
    if end <= start:
        raise ValueError("La date de fin doit être postérieure à la date de début.")
    segments: list[NationalSegment] = []
    for region in regions:
        segments.extend(_plan_region(counter, region.code, start, end))
    return segments


def _plan_region(
    counter: SegmentCounter,
    region_code: str,
    start: datetime,
    end: datetime,
) -> list[NationalSegment]:
    total = counter.count_region_segment(region_code, start, end)
    if total <= MAX_OFFERS_PER_SEGMENT:
        return [NationalSegment(region_code, start, end, total)]
    if end - start <= MIN_SEGMENT_DURATION:
        raise ValueError(
            "Segment France Travail non découplable sous le plafond de 3 150 offres."
        )
    midpoint = start + (end - start) / 2
    return _plan_region(counter, region_code, start, midpoint) + _plan_region(
        counter, region_code, midpoint, end
    )
