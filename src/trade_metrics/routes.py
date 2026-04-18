from __future__ import annotations

from typing import Any, Callable

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from trade_metrics.exceptions import UnknownMetricError, ValidationError
from trade_metrics.schemas import MetricQuery, MetricResponse, SeriesPoint
from trade_metrics.sources import MetricSource

bp = Blueprint("metrics", __name__)


@bp.get("/health")
def health() -> Any:
    return jsonify({"status": "ok"})


def _parse_query() -> MetricQuery:
    try:
        return MetricQuery.model_validate(request.args.to_dict())
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc


def _produce(metric: str, fn: Callable[[MetricQuery], list[tuple[str, float]]]) -> Any:
    q = _parse_query()
    cache = current_app.extensions["metrics_cache"]
    key = q.cache_key(metric)
    value, hit = cache.get_or_set(key, lambda: fn(q))
    response = MetricResponse(
        metric=metric,
        granularity=q.granularity,
        series=[SeriesPoint(bucket=b, value=v) for b, v in value],
        meta={
            "from": q.from_.isoformat(),
            "to": q.to.isoformat(),
            "cached": hit,
            "port": q.port,
            "country": q.country,
            "importer_id": q.importer_id,
        },
    )
    return jsonify(response.model_dump())


def _source() -> MetricSource:
    return current_app.extensions["metrics_source"]


@bp.get("/metrics/volume")
def volume() -> Any:
    return _produce("volume", _source().volume)


@bp.get("/metrics/duty-collected")
def duty_collected() -> Any:
    return _produce("duty_collected", _source().duty_collected)


@bp.get("/metrics/clearance-time")
def clearance_time() -> Any:
    return _produce("clearance_time", _source().clearance_time)


@bp.get("/metrics/rejection-rate")
def rejection_rate() -> Any:
    return _produce("rejection_rate", _source().rejection_rate)


@bp.get("/metrics/top-hs-chapters")
def top_hs_chapters() -> Any:
    return _produce("top_hs_chapters", _source().top_hs_chapters)


@bp.app_errorhandler(ValidationError)
def _on_validation_error(exc: ValidationError) -> Any:
    return jsonify({"error": "validation_error", "detail": exc.message}), exc.status_code


@bp.app_errorhandler(UnknownMetricError)
def _on_unknown_metric(exc: UnknownMetricError) -> Any:
    return jsonify({"error": "unknown_metric", "detail": exc.message}), exc.status_code
