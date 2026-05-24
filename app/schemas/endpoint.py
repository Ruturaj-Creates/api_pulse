"""Request/response shapes for monitored endpoint CRUD."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import EndpointStatus, HttpMethod


class EndpointCreate(BaseModel):
    """Body for POST /endpoints"""

    name: str = Field(min_length=1, max_length=255, examples=["GitHub API"])
    url: HttpUrl = Field(examples=["https://api.github.com/zen"])
    http_method: HttpMethod = HttpMethod.GET
    expected_status_code: int = Field(default=200, ge=100, le=599)
    check_interval_seconds: int = Field(
        default=60,
        ge=30,
        le=86400,
        description="How often to check (30 seconds to 24 hours)",
    )


class EndpointUpdate(BaseModel):
    """Body for PATCH /endpoints/{id} — all fields optional"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    http_method: HttpMethod | None = None
    expected_status_code: int | None = Field(default=None, ge=100, le=599)
    check_interval_seconds: int | None = Field(default=None, ge=30, le=86400)


class EndpointResponse(BaseModel):
    """Endpoint returned to the client (includes live monitoring state)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    url: str
    http_method: HttpMethod
    expected_status_code: int
    check_interval_seconds: int
    status: EndpointStatus
    consecutive_failures: int
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime
