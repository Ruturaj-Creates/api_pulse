"""
Import all models so Alembic sees them on Base.metadata.

Always import new models here when you add a table.
"""

from app.db.base import Base
from app.models.alert import Alert
from app.models.endpoint import Endpoint
from app.models.enums import AlertType, EndpointStatus, HttpMethod
from app.models.monitoring_log import MonitoringLog
from app.models.user import User

__all__ = [
    "Alert",
    "AlertType",
    "Base",
    "Endpoint",
    "EndpointStatus",
    "HttpMethod",
    "MonitoringLog",
    "User",
]
