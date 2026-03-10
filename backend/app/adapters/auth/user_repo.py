"""SQLAlchemy-адаптер репозитория пользователей."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


class SqlAlchemyUserRepo:
    """Репозиторий пользователей на базе SQLAlchemy AsyncSession."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Инициализирует репозиторий с активной DB-сессией."""
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает активного пользователя по email либо None."""
        statement = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(self, *, email: str, password_hash: str) -> User:
        """Создает пользователя и возвращает ORM-сущность."""
        user = User(email=email, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        return user
