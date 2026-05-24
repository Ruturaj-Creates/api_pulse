"""
Dashboard aggregates from monitoring_logs and alerts.

All stats are scoped to the authenticated user's endpoints.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.endpoint import Endpoint
from app.models.enums import EndpointStatus
from app.models.monitoring_log import MonitoringLog
from app.schemas.alert import AlertResponse, IncidentResponse
from app.schemas.dashboard import DashboardSummary, EndpointDashboardStats
from app.services import alert_service


def _period_start(hours: int) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


async def _log_stats_for_endpoints(
    db: AsyncSession,
    endpoint_ids: list[int],
    since: datetime,
) -> dict[int, dict]:
    """Aggregate check stats per endpoint_id."""
    if not endpoint_ids:
        return {}

    result = await db.execute(
        select(
            MonitoringLog.endpoint_id,
            func.count(MonitoringLog.id).label("total_checks"),
            func.sum(case((MonitoringLog.is_up.is_(True), 1), else_=0)).label("successful"),
            func.sum(case((MonitoringLog.is_up.is_(False), 1), else_=0)).label("failures"),
            func.avg(MonitoringLog.response_time_ms).label("avg_response_ms"),
        )
        .where(
            MonitoringLog.endpoint_id.in_(endpoint_ids),
            MonitoringLog.checked_at >= since,
        )
        .group_by(MonitoringLog.endpoint_id)
    )

    stats: dict[int, dict] = {}
    for row in result.all():
        total = int(row.total_checks or 0)
        successful = int(row.successful or 0)
        uptime = round((successful / total) * 100, 2) if total > 0 else 0.0
        stats[row.endpoint_id] = {
            "total_checks": total,
            "total_failures": int(row.failures or 0),
            "uptime_percentage": uptime,
            "average_response_time_ms": (
                round(float(row.avg_response_ms), 2) if row.avg_response_ms is not None else None
            ),
        }
    return stats


async def _open_alert_counts(
    db: AsyncSession,
    endpoint_ids: list[int],
) -> dict[int, int]:
    if not endpoint_ids:
        return {}

    result = await db.execute(
        select(Alert.endpoint_id, func.count(Alert.id).label("open_count"))
        .where(
            Alert.endpoint_id.in_(endpoint_ids),
            Alert.is_resolved.is_(False),
        )
        .group_by(Alert.endpoint_id)
    )
    return {row.endpoint_id: int(row.open_count) for row in result.all()}


def _endpoint_stats_row(
    endpoint: Endpoint,
    log_stats: dict[int, dict],
    open_alerts: dict[int, int],
) -> EndpointDashboardStats:
    stats = log_stats.get(endpoint.id, {})
    return EndpointDashboardStats(
        endpoint_id=endpoint.id,
        name=endpoint.name,
        url=endpoint.url,
        status=endpoint.status,
        uptime_percentage=stats.get("uptime_percentage", 0.0),
        average_response_time_ms=stats.get("average_response_time_ms"),
        total_checks=stats.get("total_checks", 0),
        total_failures=stats.get("total_failures", 0),
        open_alerts=open_alerts.get(endpoint.id, 0),
        last_checked_at=endpoint.last_checked_at,
    )


async def get_user_dashboard(
    db: AsyncSession,
    user_id: int,
    hours: int = 24,
    incident_limit: int = 10,
) -> DashboardSummary:
    """Full dashboard for all endpoints owned by the user."""
    since = _period_start(hours)

    result = await db.execute(
        select(Endpoint).where(Endpoint.user_id == user_id).order_by(Endpoint.name)
    )
    endpoints = list(result.scalars().all())
    endpoint_ids = [ep.id for ep in endpoints]

    log_stats = await _log_stats_for_endpoints(db, endpoint_ids, since)
    open_alerts = await _open_alert_counts(db, endpoint_ids)

    endpoint_rows = [
        _endpoint_stats_row(ep, log_stats, open_alerts) for ep in endpoints
    ]

    total_checks = sum(r.total_checks for r in endpoint_rows)
    total_failures = sum(r.total_failures for r in endpoint_rows)
    successful = total_checks - total_failures
    overall_uptime = round((successful / total_checks) * 100, 2) if total_checks > 0 else 0.0

    response_times = [
        r.average_response_time_ms
        for r in endpoint_rows
        if r.average_response_time_ms is not None and r.total_checks > 0
    ]
    avg_response = round(sum(response_times) / len(response_times), 2) if response_times else None

    incident_rows = await alert_service.list_recent_incidents(db, user_id, incident_limit)
    recent_incidents = [
        IncidentResponse(
            alert=AlertResponse.model_validate(alert),
            endpoint_name=endpoint.name,
            endpoint_url=endpoint.url,
            endpoint_status=endpoint.status.value,
        )
        for alert, endpoint in incident_rows
    ]

    status_counts = {s: 0 for s in EndpointStatus}
    for ep in endpoints:
        status_counts[ep.status] += 1

    return DashboardSummary(
        period_hours=hours,
        total_endpoints=len(endpoints),
        endpoints_up=status_counts[EndpointStatus.UP],
        endpoints_down=status_counts[EndpointStatus.DOWN],
        endpoints_paused=status_counts[EndpointStatus.PAUSED],
        endpoints_unknown=status_counts[EndpointStatus.UNKNOWN],
        overall_uptime_percentage=overall_uptime,
        average_response_time_ms=avg_response,
        total_checks=total_checks,
        total_failures=total_failures,
        open_alerts=sum(open_alerts.values()),
        endpoints=endpoint_rows,
        recent_incidents=recent_incidents,
    )


async def get_endpoint_dashboard(
    db: AsyncSession,
    endpoint: Endpoint,
    hours: int = 24,
) -> EndpointDashboardStats:
    """Stats for a single endpoint (caller must verify ownership)."""
    since = _period_start(hours)
    log_stats = await _log_stats_for_endpoints(db, [endpoint.id], since)
    open_alerts = await _open_alert_counts(db, [endpoint.id])
    return _endpoint_stats_row(endpoint, log_stats, open_alerts)
