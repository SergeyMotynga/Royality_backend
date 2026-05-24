"""CRUD refresh-сессий auth-домена."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.refresh_session import RefreshSession


class RefreshSessionCrud:
    """CRUD refresh-сессий на базе SQLAlchemy AsyncSession."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Инициализирует CRUD с активной DB-сессией."""
        self.session = session

    async def create_session(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshSession:
        """Создает refresh-сессию и возвращает ORM-сущность."""
        refresh_session = RefreshSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session

    async def get_active_by_token_hash(self, *, token_hash: str) -> RefreshSession | None:
        """Возвращает активную refresh-сессию по хэшу токена либо None."""
        now = datetime.now(UTC)
        statement = select(RefreshSession).where(
            RefreshSession.token_hash == token_hash,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_by_id(self, *, session_id: UUID) -> RefreshSession | None:
        """Возвращает активную refresh-сессию по id либо None."""
        now = datetime.now(UTC)
        statement = select(RefreshSession).where(
            RefreshSession.id == session_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_session(self, *, refresh_session: RefreshSession) -> RefreshSession:
        """Отзывает refresh-сессию, если она еще активна."""
        if refresh_session.revoked_at is None:
            refresh_session.revoked_at = datetime.now(UTC)
            await self.session.flush()
        return refresh_session
