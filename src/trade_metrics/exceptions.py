from __future__ import annotations


class TradeMetricsError(Exception):
    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(TradeMetricsError):
    status_code = 400


class UnknownMetricError(TradeMetricsError):
    status_code = 404


class SourceUnavailableError(TradeMetricsError):
    status_code = 503
