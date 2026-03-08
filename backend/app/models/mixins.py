"""Переиспользуемые ORM-миксины."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Добавляет UUID первичный ключ."""

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class CreatedAtMixin:
    """Добавляет поле времени создания записи."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TimestampMixin(CreatedAtMixin):
    """Добавляет поля времени создания и обновления записи."""

    # TODO(auth): Перевести обновление updated_at на DB-trigger в миграции.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class SoftDeleteMixin:
    """Добавляет поле мягкого удаления записи."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
