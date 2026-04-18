from __future__ import annotations

from datetime import date, timedelta
from typing import Iterator, Literal

from dateutil.relativedelta import relativedelta

Granularity = Literal["day", "week", "month"]
VALID_GRANULARITIES: tuple[Granularity, ...] = ("day", "week", "month")


def normalize_bucket(d: date, granularity: Granularity) -> date:
    if granularity == "day":
        return d
    if granularity == "week":
        return d - timedelta(days=d.weekday())
    if granularity == "month":
        return d.replace(day=1)
    raise ValueError(f"Unsupported granularity: {granularity}")


def step(granularity: Granularity) -> timedelta | relativedelta:
    if granularity == "day":
        return timedelta(days=1)
    if granularity == "week":
        return timedelta(days=7)
    if granularity == "month":
        return relativedelta(months=1)
    raise ValueError(f"Unsupported granularity: {granularity}")


def iter_buckets(
    start: date, end: date, granularity: Granularity
) -> Iterator[date]:
    if start >= end:
        return
    current = normalize_bucket(start, granularity)
    delta = step(granularity)
    while current < end:
        yield current
        current = current + delta


def format_bucket(d: date) -> str:
    return d.isoformat()
