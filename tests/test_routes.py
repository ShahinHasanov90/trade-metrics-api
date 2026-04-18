from __future__ import annotations

from datetime import date

import pytest

from trade_metrics.app import create_app
from trade_metrics.cache import TTLLRUCache
from trade_metrics.sources import Declaration, InMemoryMetricSource


@pytest.fixture()
def client():
    declarations = [
        Declaration(
            declared_on=date(2025, 1, 1),
            port="AZBAK",
            country="TR",
            importer_id="IMP1000",
            hs_chapter="27",
            duty_amount=100.0,
            clearance_hours=6.0,
            rejected=False,
        ),
        Declaration(
            declared_on=date(2025, 1, 1),
            port="AZBAK",
            country="TR",
            importer_id="IMP1001",
            hs_chapter="84",
            duty_amount=50.0,
            clearance_hours=10.0,
            rejected=True,
        ),
        Declaration(
            declared_on=date(2025, 1, 2),
            port="AZGCJ",
            country="RU",
            importer_id="IMP1002",
            hs_chapter="27",
            duty_amount=200.0,
            clearance_hours=4.0,
            rejected=False,
        ),
    ]
    app = create_app(
        source=InMemoryMetricSource(declarations),
        cache=TTLLRUCache(maxsize=32, ttl=60.0),
    )
    app.testing = True
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_volume_returns_zero_filled_series(client):
    resp = client.get(
        "/metrics/volume?from=2025-01-01&to=2025-01-04&granularity=day"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["metric"] == "volume"
    assert body["granularity"] == "day"
    buckets = [p["bucket"] for p in body["series"]]
    assert buckets == ["2025-01-01", "2025-01-02", "2025-01-03"]
    values = [p["value"] for p in body["series"]]
    assert values == [2.0, 1.0, 0.0]


def test_duty_collected_filters_by_country(client):
    resp = client.get(
        "/metrics/duty-collected?from=2025-01-01&to=2025-01-03&granularity=day&country=TR"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["series"][0]["value"] == 150.0
    assert body["series"][1]["value"] == 0.0


def test_rejection_rate(client):
    resp = client.get(
        "/metrics/rejection-rate?from=2025-01-01&to=2025-01-03&granularity=day"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["series"][0]["value"] == 0.5
    assert body["series"][1]["value"] == 0.0


def test_top_hs_chapters(client):
    resp = client.get(
        "/metrics/top-hs-chapters?from=2025-01-01&to=2025-01-03&granularity=day"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    labels = [p["bucket"] for p in body["series"]]
    assert labels[0] == "27"
    assert body["series"][0]["value"] == 2.0


def test_invalid_range_returns_400(client):
    resp = client.get(
        "/metrics/volume?from=2025-02-01&to=2025-01-01&granularity=day"
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"


def test_unknown_granularity_returns_400(client):
    resp = client.get(
        "/metrics/volume?from=2025-01-01&to=2025-01-02&granularity=hour"
    )
    assert resp.status_code == 400


def test_cache_marks_second_call_as_cached(client):
    url = "/metrics/volume?from=2025-01-01&to=2025-01-04&granularity=day"
    first = client.get(url).get_json()
    second = client.get(url).get_json()
    assert first["meta"]["cached"] is False
    assert second["meta"]["cached"] is True
