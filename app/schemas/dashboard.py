"""Dashboard API response shapes."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EndpointStatus
from app.schemas.alert import IncidentResponse


class EndpointDashboardStats(BaseModel):
    endpoint_id: int
    name: str
    url: str
    status: EndpointStatus
    uptime_percentage: float = Field(description="Percentage of successful checks in the period")
    average_response_time_ms: float | None
    total_checks: int
    total_failures: int
    open_alerts: int
    last_checked_at: datetime | None


class DashboardSummary(BaseModel):
    """Account-wide monitoring overview."""

    period_hours: int
    total_endpoints: int
    endpoints_up: int
    endpoints_down: int
    endpoints_paused: int
    endpoints_unknown: int
    overall_uptime_percentage: float
    average_response_time_ms: float | None
    total_checks: int
    total_failures: int
    open_alerts: int
    endpoints: list[EndpointDashboardStats]
    recent_incidents: list[IncidentResponse]
