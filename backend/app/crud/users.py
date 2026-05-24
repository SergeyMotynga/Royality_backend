"""CRUD пользователей auth-домена."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


class UserCrud:
    """CRUD пользователей на базе SQLAlchemy AsyncSession."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Инициализирует CRUD с активной DB-сессией."""
        self.session = session

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        """Возвращает активного пользователя по номеру телефона либо None."""
        statement = select(User).where(
            User.phone_number == phone_number,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Возвращает активного пользователя по id либо None."""
        statement = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        phone_number: str,
        is_verified: bool = False,
    ) -> User:
        """Создает пользователя и возвращает ORM-сущность."""
        user = User(
            phone_number=phone_number,
            is_verified=is_verified,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def mark_user_verified(self, *, user: User) -> User:
        """Помечает пользователя как верифицированного."""
        user.is_verified = True
        await self.session.flush()
        return user
