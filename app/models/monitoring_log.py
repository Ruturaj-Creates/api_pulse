"""History of every health check — powers dashboards and uptime stats."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.endpoint import Endpoint


class MonitoringLog(Base):
    __tablename__ = "monitoring_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("endpoints.id", ondelete="CASCADE"),
        index=True,
    )

    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_up: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    endpoint: Mapped["Endpoint"] = relationship(back_populates="monitoring_logs")
