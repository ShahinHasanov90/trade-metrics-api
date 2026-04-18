# trade-metrics-api

A read-heavy metrics API that exposes customs trade KPIs over HTTP. It sits in
front of the data warehouse and feeds operational dashboards with cached,
time-bucketed series data.

## Domain

The service aggregates declaration-level customs data into time series for a
fixed set of KPIs. Every metric is computed against a time window and returned
as an ordered list of buckets.

Supported metrics:

- Declaration volume (count of declarations)
- Duty collected (sum of duty amounts)
- Average clearance time (mean hours between submission and release)
- Rejection rate (rejected / total)
- Top HS chapters (ranked by volume, returned as a single bucket)

Every query accepts:

- `from` (ISO-8601 date, inclusive)
- `to` (ISO-8601 date, exclusive)
- `granularity` (`day`, `week`, `month`)
- optional `port` (customs post code)
- optional `country` (ISO-2 origin country)
- optional `importer_id` (tax id)

## Response format

```json
{
  "metric": "volume",
  "granularity": "day",
  "series": [
    {"bucket": "2025-01-01", "value": 1423},
    {"bucket": "2025-01-02", "value": 1510}
  ],
  "meta": {"from": "2025-01-01", "to": "2025-01-03", "cached": false}
}
```

## Endpoints

- `GET /health`
- `GET /metrics/volume`
- `GET /metrics/duty-collected`
- `GET /metrics/clearance-time`
- `GET /metrics/rejection-rate`
- `GET /metrics/top-hs-chapters`

## Caching

Expensive queries are wrapped in an in-process TTL LRU cache keyed by the full
query signature. Default TTL is 60 seconds. The `meta.cached` flag indicates
whether the response was served from cache.

## Running

```bash
pip install -e .
FLASK_APP=trade_metrics.app:create_app flask run --port 8080
```

Or with Docker:

```bash
docker build -t trade-metrics-api .
docker run --rm -p 8080:8080 trade-metrics-api
```

## curl examples

```bash
curl "http://localhost:8080/health"

curl "http://localhost:8080/metrics/volume?from=2025-01-01&to=2025-02-01&granularity=day"

curl "http://localhost:8080/metrics/duty-collected?from=2025-01-01&to=2025-04-01&granularity=week&country=TR"

curl "http://localhost:8080/metrics/clearance-time?from=2025-01-01&to=2025-02-01&granularity=day&port=AZBAK"

curl "http://localhost:8080/metrics/rejection-rate?from=2025-01-01&to=2025-02-01&granularity=month"

curl "http://localhost:8080/metrics/top-hs-chapters?from=2025-01-01&to=2025-02-01&granularity=month"
```

## Testing

```bash
pytest -q
```

## Extending

Swap `InMemoryMetricSource` for a warehouse-backed implementation by
subclassing `MetricSource` and wiring it in `create_app`.
