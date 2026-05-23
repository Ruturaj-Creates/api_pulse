"""User account — owns monitored endpoints."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.endpoint import Endpoint


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    # One user → many endpoints (delete endpoints when user is deleted)
    endpoints: Mapped[list["Endpoint"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
