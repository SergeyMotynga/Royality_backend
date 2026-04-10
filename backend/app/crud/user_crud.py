"""CRUD-операции для сущности пользователя."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.user_follower import UserFollower


class UserCrud:
    """Доступ к данным пользователей."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_login(self, login: str) -> User | None:
        """Возвращает пользователя по логину."""
        stmt = select(User).where(User.login == login)
        return self._session.scalar(stmt)

    def get_by_id(self, user_id: UUID) -> User | None:
        """Возвращает пользователя по идентификатору."""
        return self._session.get(User, user_id)

    def create_user(self, login: str, password_hash: str, name: str) -> User:
        """Создает пользователя и возвращает сохраненную сущность."""
        user = User(login=login, password_hash=password_hash, name=name)
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def update_profile(
        self,
        user: User,
        nickname: str,
        avatar_url: str | None,
        bio: str | None,
        level: int,
    ) -> User:
        """Обновляет профиль пользователя."""
        user.name = nickname
        user.avatar_url = avatar_url
        user.bio = bio
        user.level = level
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def add_follower(self, follower_id: UUID, followee_id: UUID) -> bool:
        """Создает подписку пользователя на пользователя."""
        if follower_id == followee_id:
            return False

        existing_relation = self._session.get(UserFollower, (follower_id, followee_id))
        if existing_relation is not None:
            return False

        relation = UserFollower(follower_id=follower_id, followee_id=followee_id)
        self._session.add(relation)
        self._session.commit()
        return True

    def count_followers(self, user_id: UUID) -> int:
        """Возвращает количество подписчиков пользователя."""
        stmt = (
            select(func.count())
            .select_from(UserFollower)
            .where(UserFollower.followee_id == user_id)
        )
        return int(self._session.scalar(stmt) or 0)

    def is_following(self, follower_id: UUID, followee_id: UUID) -> bool:
        """Проверяет, подписан ли пользователь на другого пользователя."""
        if follower_id == followee_id:
            return False

        stmt = select(func.count()).select_from(UserFollower).where(
            UserFollower.follower_id == follower_id,
            UserFollower.followee_id == followee_id,
        )
        return int(self._session.scalar(stmt) or 0) > 0

    def remove_follower(self, follower_id: UUID, followee_id: UUID) -> bool:
        """Удаляет подписку пользователя на пользователя."""
        relation = self._session.get(UserFollower, (follower_id, followee_id))
        if relation is None:
            return False
        self._session.delete(relation)
        self._session.commit()
        return True
