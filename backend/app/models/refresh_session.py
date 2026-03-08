"""ORM-модель refresh-сессии пользователя."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.models.user import User


class RefreshSession(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    """Refresh-сессия для продления авторизации."""

    __tablename__ = "refresh_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship(
        "User",
        back_populates="refresh_sessions",
        lazy="selectin",
    )
