"""
CRUD for monitored endpoints.

Every query filters by user_id so users cannot access each other's data.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.endpoint import Endpoint
from app.models.enums import EndpointStatus
from app.models.user import User
from app.schemas.endpoint import EndpointCreate, EndpointUpdate


async def list_endpoints_for_user(
    db: AsyncSession,
    user_id: int,
) -> list[Endpoint]:
    result = await db.execute(
        select(Endpoint)
        .where(Endpoint.user_id == user_id)
        .order_by(Endpoint.created_at.desc())
    )
    return list(result.scalars().all())


async def get_endpoint_for_user(
    db: AsyncSession,
    endpoint_id: int,
    user_id: int,
) -> Endpoint | None:
    result = await db.execute(
        select(Endpoint).where(
            Endpoint.id == endpoint_id,
            Endpoint.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_endpoint(
    db: AsyncSession,
    user: User,
    data: EndpointCreate,
    settings: Settings,
) -> Endpoint:
    endpoint = Endpoint(
        user_id=user.id,
        name=data.name,
        url=str(data.url),
        http_method=data.http_method,
        expected_status_code=data.expected_status_code,
        check_interval_seconds=data.check_interval_seconds
        or settings.default_check_interval_seconds,
        status=EndpointStatus.UNKNOWN,
    )
    db.add(endpoint)
    await db.flush()
    await db.refresh(endpoint)
    return endpoint


async def update_endpoint(
    db: AsyncSession,
    endpoint: Endpoint,
    data: EndpointUpdate,
) -> Endpoint:
    """Apply only fields the client sent (partial update)."""
    update_data = data.model_dump(exclude_unset=True)
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])

    for field, value in update_data.items():
        setattr(endpoint, field, value)

    await db.flush()
    await db.refresh(endpoint)
    return endpoint


async def delete_endpoint(db: AsyncSession, endpoint: Endpoint) -> None:
    await db.delete(endpoint)


async def pause_endpoint(db: AsyncSession, endpoint: Endpoint) -> Endpoint:
    endpoint.status = EndpointStatus.PAUSED
    await db.flush()
    await db.refresh(endpoint)
    return endpoint


async def resume_endpoint(db: AsyncSession, endpoint: Endpoint) -> Endpoint:
    endpoint.status = EndpointStatus.UNKNOWN
    endpoint.consecutive_failures = 0
    await db.flush()
    await db.refresh(endpoint)
    return endpoint
