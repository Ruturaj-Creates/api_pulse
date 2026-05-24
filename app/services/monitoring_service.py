"""
Run health checks, persist logs, and update endpoint status.

Called by the background scheduler and the manual /check API.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.endpoint import Endpoint
from app.models.enums import EndpointStatus
from app.models.monitoring_log import MonitoringLog
from app.services.health_checker import perform_health_check


async def list_endpoints_due_for_check(db: AsyncSession) -> list[Endpoint]:
    """All non-paused endpoints (scheduler filters by interval)."""
    result = await db.execute(
        select(Endpoint).where(Endpoint.status != EndpointStatus.PAUSED)
    )
    return list(result.scalars().all())


def is_endpoint_due(endpoint: Endpoint, now: datetime) -> bool:
    """True if never checked or interval has elapsed."""
    if endpoint.last_checked_at is None:
        return True
    elapsed = (now - endpoint.last_checked_at).total_seconds()
    return elapsed >= endpoint.check_interval_seconds


async def get_endpoint_by_id(db: AsyncSession, endpoint_id: int) -> Endpoint | None:
    result = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    return result.scalar_one_or_none()


async def run_health_check(
    db: AsyncSession,
    endpoint: Endpoint,
    settings: Settings | None = None,
) -> MonitoringLog | None:
    """
    Check one endpoint, save a log row, update endpoint state.

    Returns None if endpoint is paused (skipped).
    """
    if settings is None:
        settings = get_settings()

    if endpoint.status == EndpointStatus.PAUSED:
        return None

    result = await perform_health_check(
        endpoint,
        timeout_seconds=settings.health_check_timeout_seconds,
        max_retries=settings.health_check_max_retries,
    )

    now = datetime.now(UTC)
    log = MonitoringLog(
        endpoint_id=endpoint.id,
        response_time_ms=result.response_time_ms,
        status_code=result.status_code,
        is_up=result.is_up,
        failure_reason=result.failure_reason,
        checked_at=now,
    )
    db.add(log)

    endpoint.last_checked_at = now

    if result.is_up:
        endpoint.status = EndpointStatus.UP
        endpoint.consecutive_failures = 0
    else:
        endpoint.consecutive_failures += 1
        if endpoint.consecutive_failures >= settings.failure_threshold:
            endpoint.status = EndpointStatus.DOWN
        elif endpoint.status != EndpointStatus.DOWN:
            # Still failing but not yet marked DOWN
            endpoint.status = EndpointStatus.UNKNOWN

    await db.flush()
    await db.refresh(log)
    await db.refresh(endpoint)
    return log


async def list_logs_for_endpoint(
    db: AsyncSession,
    endpoint_id: int,
    limit: int = 50,
) -> list[MonitoringLog]:
    result = await db.execute(
        select(MonitoringLog)
        .where(MonitoringLog.endpoint_id == endpoint_id)
        .order_by(MonitoringLog.checked_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
