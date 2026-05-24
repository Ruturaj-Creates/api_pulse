"""
Background scheduler — periodically checks due endpoints.

Uses APScheduler's AsyncIOScheduler so jobs run on the same event loop as FastAPI.
"""

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services import monitoring_service

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def run_due_health_checks() -> None:
    """
    Load due endpoints and check them concurrently.

    Each check uses its own DB session to avoid sharing state across tasks.
    """
    settings = get_settings()
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session:
        endpoints = await monitoring_service.list_endpoints_due_for_check(session)

    due = [ep for ep in endpoints if monitoring_service.is_endpoint_due(ep, now)]
    if not due:
        return

    logger.info("Running health checks for %d endpoint(s)", len(due))
    semaphore = asyncio.Semaphore(settings.max_concurrent_checks)

    async def check_one(endpoint_id: int) -> None:
        async with semaphore:
            async with AsyncSessionLocal() as session:
                endpoint = await monitoring_service.get_endpoint_by_id(
                    session, endpoint_id
                )
                if endpoint is None:
                    return
                try:
                    await monitoring_service.run_health_check(
                        session, endpoint, settings
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception(
                        "Health check failed for endpoint id=%s", endpoint_id
                    )

    await asyncio.gather(*(check_one(ep.id) for ep in due))


def start_scheduler() -> AsyncIOScheduler:
    """Start interval job and return scheduler instance."""
    global _scheduler

    settings = get_settings()
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_due_health_checks,
        trigger="interval",
        seconds=settings.scheduler_tick_seconds,
        id="health_checks",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — tick every %ss, max %s concurrent checks",
        settings.scheduler_tick_seconds,
        settings.max_concurrent_checks,
    )
    return _scheduler


def stop_scheduler() -> None:
    """Shut down scheduler on app exit."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
