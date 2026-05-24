"""Monitoring log API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonitoringLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint_id: int
    response_time_ms: int | None
    status_code: int | None
    is_up: bool
    failure_reason: str | None
    checked_at: datetime
