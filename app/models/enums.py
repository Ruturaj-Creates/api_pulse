"""Shared enums for database columns."""

import enum


class HttpMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"


class EndpointStatus(str, enum.Enum):
    """Current health state of a monitored endpoint."""

    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    PAUSED = "paused"


class AlertType(str, enum.Enum):
    EMAIL = "email"
