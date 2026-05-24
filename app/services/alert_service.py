"""
Alert creation, resolution, and listing.

Alerts fire once when an endpoint transitions to DOWN (not on every failed check).
Open alerts auto-resolve when the endpoint recovers.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.alert import Alert
from app.models.endpoint import Endpoint
from app.models.enums import AlertType
from app.services.auth_service import get_user_by_id
from app.utils.email import send_email

logger = logging.getLogger(__name__)


async def get_unresolved_alert_for_endpoint(
    db: AsyncSession,
    endpoint_id: int,
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.endpoint_id == endpoint_id,
            Alert.is_resolved.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def create_down_alert(
    db: AsyncSession,
    endpoint: Endpoint,
    failure_reason: str | None,
    settings: Settings,
) -> Alert | None:
    """
    Create alert + send email when endpoint first goes DOWN.

    Skips if an unresolved alert already exists (no spam).
    """
    existing = await get_unresolved_alert_for_endpoint(db, endpoint.id)
    if existing is not None:
        return existing

    user = await get_user_by_id(db, endpoint.user_id)
    if user is None:
        logger.warning("No user for endpoint id=%s — alert skipped", endpoint.id)
        return None

    reason = failure_reason or "Unknown failure"
    message = (
        f"Endpoint '{endpoint.name}' is DOWN.\n"
        f"URL: {endpoint.url}\n"
        f"Reason: {reason}\n"
        f"Consecutive failures: {endpoint.consecutive_failures}"
    )

    alert = Alert(
        user_id=endpoint.user_id,
        endpoint_id=endpoint.id,
        alert_type=AlertType.EMAIL,
        message=message,
        is_resolved=False,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)

    subject = f"[API Pulse] DOWN: {endpoint.name}"
    await send_email(user.email, subject, message, settings)
    logger.info("Down alert created for endpoint id=%s user=%s", endpoint.id, user.email)
    return alert


async def resolve_alerts_for_endpoint(
    db: AsyncSession,
    endpoint: Endpoint,
    settings: Settings,
) -> int:
    """Mark all open alerts resolved when endpoint recovers. Returns count resolved."""
    result = await db.execute(
        select(Alert).where(
            Alert.endpoint_id == endpoint.id,
            Alert.is_resolved.is_(False),
        )
    )
    alerts = list(result.scalars().all())
    if not alerts:
        return 0

    user = await get_user_by_id(db, endpoint.user_id)
    for alert in alerts:
        alert.is_resolved = True

    await db.flush()

    if user is not None:
        subject = f"[API Pulse] RECOVERED: {endpoint.name}"
        body = (
            f"Endpoint '{endpoint.name}' is back UP.\n"
            f"URL: {endpoint.url}\n"
            f"Resolved {len(alerts)} open alert(s)."
        )
        await send_email(user.email, subject, body, settings)

    logger.info("Resolved %d alert(s) for endpoint id=%s", len(alerts), endpoint.id)
    return len(alerts)


async def list_alerts_for_user(
    db: AsyncSession,
    user_id: int,
    resolved: bool | None = None,
    limit: int = 50,
) -> list[Alert]:
    query = select(Alert).where(Alert.user_id == user_id).order_by(Alert.sent_at.desc())

    if resolved is True:
        query = query.where(Alert.is_resolved.is_(True))
    elif resolved is False:
        query = query.where(Alert.is_resolved.is_(False))

    query = query.limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_alert_for_user(
    db: AsyncSession,
    alert_id: int,
    user_id: int,
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def resolve_alert(db: AsyncSession, alert: Alert) -> Alert:
    alert.is_resolved = True
    await db.flush()
    await db.refresh(alert)
    return alert


async def list_recent_incidents(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[tuple[Alert, Endpoint]]:
    """
    Recent alerts with endpoint details — powers incident views.

    Includes unresolved alerts and recently resolved ones.
    """
    result = await db.execute(
        select(Alert, Endpoint)
        .join(Endpoint, Alert.endpoint_id == Endpoint.id)
        .where(Alert.user_id == user_id)
        .order_by(Alert.is_resolved.asc(), Alert.sent_at.desc())
        .limit(limit)
    )
    return list(result.all())
