"""Alert record when an endpoint stays down after repeated failures."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AlertType

if TYPE_CHECKING:
    from app.models.endpoint import Endpoint
    from app.models.user import User


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("endpoints.id", ondelete="CASCADE"),
        index=True,
    )

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", native_enum=False),
        default=AlertType.EMAIL,
    )
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="alerts")
    endpoint: Mapped["Endpoint"] = relationship(back_populates="alerts")
