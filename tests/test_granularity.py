from __future__ import annotations

from datetime import date

import pytest

from trade_metrics.granularity import (
    format_bucket,
    iter_buckets,
    normalize_bucket,
)


def test_normalize_day_is_identity():
    d = date(2025, 3, 12)
    assert normalize_bucket(d, "day") == d


def test_normalize_week_snaps_to_monday():
    assert normalize_bucket(date(2025, 3, 12), "week") == date(2025, 3, 10)
    assert normalize_bucket(date(2025, 3, 10), "week") == date(2025, 3, 10)


def test_normalize_month_snaps_to_first():
    assert normalize_bucket(date(2025, 3, 27), "month") == date(2025, 3, 1)


def test_iter_buckets_daily_range():
    buckets = list(iter_buckets(date(2025, 1, 1), date(2025, 1, 4), "day"))
    assert buckets == [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]


def test_iter_buckets_monthly_spans_quarter():
    buckets = list(iter_buckets(date(2025, 1, 15), date(2025, 4, 1), "month"))
    assert buckets == [date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)]


def test_iter_buckets_empty_when_start_not_before_end():
    assert list(iter_buckets(date(2025, 1, 2), date(2025, 1, 2), "day")) == []


def test_unsupported_granularity_raises():
    with pytest.raises(ValueError):
        normalize_bucket(date(2025, 1, 1), "quarter")  # type: ignore[arg-type]


def test_format_bucket():
    assert format_bucket(date(2025, 1, 1)) == "2025-01-01"
