from __future__ import annotations

from typing import Any

from flask import Flask

from trade_metrics.cache import TTLLRUCache
from trade_metrics.routes import bp
from trade_metrics.sources import InMemoryMetricSource, MetricSource


def create_app(
    source: MetricSource | None = None,
    cache: TTLLRUCache | None = None,
    config: dict[str, Any] | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config.setdefault("JSON_SORT_KEYS", False)
    if config:
        app.config.update(config)

    app.extensions["metrics_source"] = source or InMemoryMetricSource()
    app.extensions["metrics_cache"] = cache or TTLLRUCache(
        maxsize=app.config.get("CACHE_MAXSIZE", 256),
        ttl=app.config.get("CACHE_TTL", 60.0),
    )

    app.register_blueprint(bp)
    return app
