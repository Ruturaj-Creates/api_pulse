"""Monitored API URL — checked periodically by the health worker."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import EndpointStatus, HttpMethod

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.monitoring_log import MonitoringLog
    from app.models.user import User


class Endpoint(Base, TimestampMixin):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    http_method: Mapped[HttpMethod] = mapped_column(
        Enum(HttpMethod, name="http_method", native_enum=False),
        default=HttpMethod.GET,
    )
    expected_status_code: Mapped[int] = mapped_column(Integer, default=200)
    check_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)

    # Monitoring state (updated by the background worker in a later step)
    status: Mapped[EndpointStatus] = mapped_column(
        Enum(EndpointStatus, name="endpoint_status", native_enum=False),
        default=EndpointStatus.UNKNOWN,
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner: Mapped["User"] = relationship(back_populates="endpoints")
    monitoring_logs: Mapped[list["MonitoringLog"]] = relationship(
        back_populates="endpoint",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="endpoint",
        cascade="all, delete-orphan",
    )
