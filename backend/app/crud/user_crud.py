"""CRUD-операции для сущности пользователя."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User


class UserCrud:
    """Доступ к данным пользователей."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_login(self, login: str) -> User | None:
        """Возвращает пользователя по логину."""
        stmt = select(User).where(User.login == login)
        return self._session.scalar(stmt)

    def create_user(self, login: str, password_hash: str, name: str) -> User:
        """Создает пользователя и возвращает сохраненную сущность."""
        user = User(login=login, password_hash=password_hash, name=name)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
