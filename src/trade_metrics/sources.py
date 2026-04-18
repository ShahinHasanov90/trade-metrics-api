from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from trade_metrics.granularity import (
    Granularity,
    format_bucket,
    iter_buckets,
    normalize_bucket,
)
from trade_metrics.schemas import MetricQuery


@dataclass(frozen=True)
class Declaration:
    declared_on: date
    port: str
    country: str
    importer_id: str
    hs_chapter: str
    duty_amount: float
    clearance_hours: float
    rejected: bool


class MetricSource(ABC):
    @abstractmethod
    def volume(self, q: MetricQuery) -> list[tuple[str, float]]: ...

    @abstractmethod
    def duty_collected(self, q: MetricQuery) -> list[tuple[str, float]]: ...

    @abstractmethod
    def clearance_time(self, q: MetricQuery) -> list[tuple[str, float]]: ...

    @abstractmethod
    def rejection_rate(self, q: MetricQuery) -> list[tuple[str, float]]: ...

    @abstractmethod
    def top_hs_chapters(
        self, q: MetricQuery, limit: int = 5
    ) -> list[tuple[str, float]]: ...


def _filter(declarations: Iterable[Declaration], q: MetricQuery) -> list[Declaration]:
    result: list[Declaration] = []
    for d in declarations:
        if d.declared_on < q.from_ or d.declared_on >= q.to:
            continue
        if q.port is not None and d.port != q.port:
            continue
        if q.country is not None and d.country != q.country:
            continue
        if q.importer_id is not None and d.importer_id != q.importer_id:
            continue
        result.append(d)
    return result


class InMemoryMetricSource(MetricSource):
    def __init__(self, declarations: Iterable[Declaration] | None = None) -> None:
        self._declarations: list[Declaration] = (
            list(declarations) if declarations is not None else list(_seed())
        )

    def volume(self, q: MetricQuery) -> list[tuple[str, float]]:
        counts: dict[date, int] = defaultdict(int)
        for d in _filter(self._declarations, q):
            counts[normalize_bucket(d.declared_on, q.granularity)] += 1
        return self._zero_fill(counts, q.from_, q.to, q.granularity)

    def duty_collected(self, q: MetricQuery) -> list[tuple[str, float]]:
        totals: dict[date, float] = defaultdict(float)
        for d in _filter(self._declarations, q):
            totals[normalize_bucket(d.declared_on, q.granularity)] += d.duty_amount
        return self._zero_fill(totals, q.from_, q.to, q.granularity)

    def clearance_time(self, q: MetricQuery) -> list[tuple[str, float]]:
        sums: dict[date, float] = defaultdict(float)
        counts: dict[date, int] = defaultdict(int)
        for d in _filter(self._declarations, q):
            bucket = normalize_bucket(d.declared_on, q.granularity)
            sums[bucket] += d.clearance_hours
            counts[bucket] += 1
        series: list[tuple[str, float]] = []
        for bucket in iter_buckets(q.from_, q.to, q.granularity):
            n = counts.get(bucket, 0)
            avg = sums[bucket] / n if n else 0.0
            series.append((format_bucket(bucket), round(avg, 3)))
        return series

    def rejection_rate(self, q: MetricQuery) -> list[tuple[str, float]]:
        totals: dict[date, int] = defaultdict(int)
        rejected: dict[date, int] = defaultdict(int)
        for d in _filter(self._declarations, q):
            bucket = normalize_bucket(d.declared_on, q.granularity)
            totals[bucket] += 1
            if d.rejected:
                rejected[bucket] += 1
        series: list[tuple[str, float]] = []
        for bucket in iter_buckets(q.from_, q.to, q.granularity):
            n = totals.get(bucket, 0)
            rate = rejected[bucket] / n if n else 0.0
            series.append((format_bucket(bucket), round(rate, 4)))
        return series

    def top_hs_chapters(
        self, q: MetricQuery, limit: int = 5
    ) -> list[tuple[str, float]]:
        counter: Counter[str] = Counter()
        for d in _filter(self._declarations, q):
            counter[d.hs_chapter] += 1
        return [(chapter, float(count)) for chapter, count in counter.most_common(limit)]

    @staticmethod
    def _zero_fill(
        values: dict[date, float] | dict[date, int],
        start: date,
        end: date,
        granularity: Granularity,
    ) -> list[tuple[str, float]]:
        series: list[tuple[str, float]] = []
        for bucket in iter_buckets(start, end, granularity):
            series.append((format_bucket(bucket), float(values.get(bucket, 0))))
        return series


def _seed() -> list[Declaration]:
    base = date(2025, 1, 1)
    ports = ["AZBAK", "AZGCJ", "AZLLK"]
    countries = ["TR", "RU", "CN", "DE"]
    chapters = ["27", "84", "85", "87", "72"]
    declarations: list[Declaration] = []
    for i in range(120):
        declared_on = base + timedelta(days=i // 4)
        declarations.append(
            Declaration(
                declared_on=declared_on,
                port=ports[i % len(ports)],
                country=countries[i % len(countries)],
                importer_id=f"IMP{1000 + (i % 17):04d}",
                hs_chapter=chapters[i % len(chapters)],
                duty_amount=125.5 + (i % 9) * 37.0,
                clearance_hours=4.0 + (i % 11) * 0.75,
                rejected=(i % 13 == 0),
            )
        )
    return declarations
