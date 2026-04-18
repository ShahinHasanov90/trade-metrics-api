from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from trade_metrics.granularity import VALID_GRANULARITIES


class MetricQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    from_: date = Field(alias="from")
    to: date
    granularity: Literal["day", "week", "month"]
    port: str | None = None
    country: str | None = None
    importer_id: str | None = None

    @field_validator("granularity")
    @classmethod
    def _granularity_supported(cls, value: str) -> str:
        if value not in VALID_GRANULARITIES:
            raise ValueError(f"granularity must be one of {VALID_GRANULARITIES}")
        return value

    @field_validator("country")
    @classmethod
    def _country_iso2(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) != 2 or not value.isalpha():
            raise ValueError("country must be an ISO-2 alpha code")
        return value.upper()

    @model_validator(mode="after")
    def _range_valid(self) -> "MetricQuery":
        if self.from_ >= self.to:
            raise ValueError("from must be earlier than to")
        return self

    def cache_key(self, metric: str) -> tuple[Any, ...]:
        return (
            metric,
            self.from_.isoformat(),
            self.to.isoformat(),
            self.granularity,
            self.port,
            self.country,
            self.importer_id,
        )


class SeriesPoint(BaseModel):
    bucket: str
    value: float


class MetricResponse(BaseModel):
    metric: str
    granularity: str
    series: list[SeriesPoint]
    meta: dict[str, Any]
