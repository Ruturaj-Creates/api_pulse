"""Dashboard overview and per-endpoint stats — JWT required."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, EndpointDashboardStats
from app.services import dashboard_service, endpoint_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardSummary,
    summary="Account dashboard — uptime, failures, incidents",
)
async def get_dashboard(
    hours: int = Query(default=24, ge=1, le=720, description="Stats window in hours"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns:

    - Overall uptime % and average response time
    - Per-endpoint breakdown
    - Recent incidents
    """
    return await dashboard_service.get_user_dashboard(db, current_user.id, hours=hours)


@router.get(
    "/endpoints/{endpoint_id}",
    response_model=EndpointDashboardStats,
    summary="Dashboard stats for one endpoint",
)
async def get_endpoint_dashboard(
    endpoint_id: int,
    hours: int = Query(default=24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = await endpoint_service.get_endpoint_for_user(
        db, endpoint_id, current_user.id
    )
    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )
    return await dashboard_service.get_endpoint_dashboard(db, endpoint, hours=hours)
