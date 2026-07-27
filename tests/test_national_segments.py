from __future__ import annotations

from datetime import UTC, datetime

from candidature_emploi.application.national_segments import plan_national_segments
from candidature_emploi.domain.offers import Region


class FakeCounter:
    def count_region_segment(self, region_code, start, end):
        return 6301 if (end - start).days > 1 else 20


def test_planner_splits_a_region_until_every_segment_is_under_api_limit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 9, tzinfo=UTC)

    segments = plan_national_segments(
        FakeCounter(), [Region(code="11", label="Île-de-France")], start, end
    )

    assert len(segments) > 1
    assert all(segment.total <= 3150 for segment in segments)
    assert all(segment.region_code == "11" for segment in segments)


def test_planner_rejects_a_non_divisible_segment_above_the_api_limit() -> None:
    class OverflowingCounter:
        def count_region_segment(self, region_code, start, end):
            return 3151

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)

    try:
        plan_national_segments(
            OverflowingCounter(), [Region(code="11", label="Île-de-France")], start, end
        )
    except ValueError as error:
        assert "non découplable" in str(error)
    else:
        raise AssertionError("Le segment non découplable doit provoquer un échec.")
