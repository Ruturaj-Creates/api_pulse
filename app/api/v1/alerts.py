"""Alert and incident routes — all require JWT."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.alert import AlertResponse, IncidentResponse
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "/incidents/recent",
    response_model=list[IncidentResponse],
    summary="Recent incidents (alerts with endpoint context)",
)
async def recent_incidents(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await alert_service.list_recent_incidents(db, current_user.id, limit)
    return [
        IncidentResponse(
            alert=AlertResponse.model_validate(alert),
            endpoint_name=endpoint.name,
            endpoint_url=endpoint.url,
            endpoint_status=endpoint.status.value,
        )
        for alert, endpoint in rows
    ]


@router.get("", response_model=list[AlertResponse], summary="List your alerts")
async def list_alerts(
    resolved: bool | None = Query(
        default=None,
        description="Filter: true=resolved, false=open, omit=all",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await alert_service.list_alerts_for_user(
        db, current_user.id, resolved=resolved, limit=limit
    )


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get one alert")
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = await alert_service.get_alert_for_user(db, alert_id, current_user.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Manually mark an alert as resolved",
)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = await alert_service.get_alert_for_user(db, alert_id, current_user.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.is_resolved:
        return alert
    return await alert_service.resolve_alert(db, alert)
