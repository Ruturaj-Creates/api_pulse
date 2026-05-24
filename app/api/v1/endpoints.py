"""
Monitored endpoint CRUD — all routes require JWT.

Users can only manage their own endpoints (filtered by user_id in the service layer).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.endpoint import EndpointCreate, EndpointResponse, EndpointUpdate
from app.schemas.monitoring_log import MonitoringLogResponse
from app.services import endpoint_service, monitoring_service

router = APIRouter(prefix="/endpoints", tags=["Endpoints"])


async def _get_user_endpoint_or_404(
    endpoint_id: int,
    current_user: User,
    db: AsyncSession,
):
    endpoint = await endpoint_service.get_endpoint_for_user(
        db, endpoint_id, current_user.id
    )
    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )
    return endpoint


@router.post(
    "",
    response_model=EndpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a URL to monitor",
)
async def create_endpoint(
    body: EndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    return await endpoint_service.create_endpoint(db, current_user, body, settings)


@router.get("", response_model=list[EndpointResponse], summary="List your endpoints")
async def list_endpoints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await endpoint_service.list_endpoints_for_user(db, current_user.id)


@router.get(
    "/{endpoint_id}",
    response_model=EndpointResponse,
    summary="Get one endpoint by id",
)
async def get_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_user_endpoint_or_404(endpoint_id, current_user, db)


@router.patch(
    "/{endpoint_id}",
    response_model=EndpointResponse,
    summary="Update endpoint settings",
)
async def update_endpoint(
    endpoint_id: int,
    body: EndpointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    return await endpoint_service.update_endpoint(db, endpoint, body)


@router.delete(
    "/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an endpoint",
)
async def delete_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    await endpoint_service.delete_endpoint(db, endpoint)


@router.post(
    "/{endpoint_id}/check",
    response_model=MonitoringLogResponse,
    summary="Run a health check immediately (manual trigger)",
)
async def trigger_health_check(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    endpoint = await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    log = await monitoring_service.run_health_check(db, endpoint, settings)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint is paused",
        )
    return log


@router.get(
    "/{endpoint_id}/logs",
    response_model=list[MonitoringLogResponse],
    summary="Recent health check history for an endpoint",
)
async def list_endpoint_logs(
    endpoint_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 200",
        )
    return await monitoring_service.list_logs_for_endpoint(db, endpoint_id, limit)


@router.post(
    "/{endpoint_id}/pause",
    response_model=EndpointResponse,
    summary="Pause monitoring for an endpoint",
)
async def pause_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    return await endpoint_service.pause_endpoint(db, endpoint)


@router.post(
    "/{endpoint_id}/resume",
    response_model=EndpointResponse,
    summary="Resume monitoring for a paused endpoint",
)
async def resume_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = await _get_user_endpoint_or_404(endpoint_id, current_user, db)
    return await endpoint_service.resume_endpoint(db, endpoint)
