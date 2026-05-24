"""Alert API response shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertType


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    endpoint_id: int
    alert_type: AlertType
    message: str
    sent_at: datetime
    is_resolved: bool


class IncidentResponse(BaseModel):
    """Recent incident — alert plus endpoint context for dashboards."""

    alert: AlertResponse
    endpoint_name: str
    endpoint_url: str
    endpoint_status: str
