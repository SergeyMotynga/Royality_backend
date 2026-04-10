"""CRUD-операции для постов."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.post import Post
from backend.app.models.post_like import PostLike
from backend.app.models.post_media import PostMedia


class PostCrud:
    """Доступ к данным постов и лайков."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_post(
        self,
        author_id: UUID,
        text: str,
        medias: list[str],
        disable_comments: bool,
    ) -> Post:
        """Создает пост с медиа и возвращает сохраненную сущность."""
        post = Post(author_id=author_id, text=text, disable_comments=disable_comments)
        post.medias = [PostMedia(url=url) for url in medias]
        self._session.add(post)
        self._session.commit()
        created_post = self.get_post_by_id(post_id=post.id)
        if created_post is None:
            raise RuntimeError("Пост не удалось загрузить после создания")
        return created_post

    def get_post_by_id(self, post_id: UUID) -> Post | None:
        """Возвращает пост по идентификатору."""
        stmt = (
            select(Post)
            .where(Post.id == post_id)
            .options(
                joinedload(Post.author),
                joinedload(Post.medias),
            )
        )
        return self._session.execute(stmt).scalars().unique().first()

    def list_feed(self, limit: int, offset: int) -> list[Post]:
        """Возвращает срез ленты постов."""
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(
                joinedload(Post.author),
                joinedload(Post.medias),
            )
        )
        return list(self._session.execute(stmt).scalars().unique().all())

    def update_post(self, post: Post, text: str, medias: list[str], disable_comments: bool) -> Post:
        """Обновляет содержимое поста."""
        post.text = text
        post.disable_comments = disable_comments
        post.medias = [PostMedia(url=url) for url in medias]
        self._session.add(post)
        self._session.commit()
        updated_post = self.get_post_by_id(post_id=post.id)
        if updated_post is None:
            raise RuntimeError("Пост не удалось загрузить после обновления")
        return updated_post

    def delete_post(self, post: Post) -> None:
        """Удаляет пост."""
        self._session.delete(post)
        self._session.commit()

    def add_like(self, post_id: UUID, user_id: UUID) -> bool:
        """Добавляет лайк к посту и возвращает признак создания записи."""
        existing_like = self._session.get(PostLike, (post_id, user_id))
        if existing_like is not None:
            return False
        self._session.add(PostLike(post_id=post_id, user_id=user_id))
        self._session.commit()
        return True

    def remove_like(self, post_id: UUID, user_id: UUID) -> bool:
        """Удаляет лайк у поста и возвращает признак удаления записи."""
        existing_like = self._session.get(PostLike, (post_id, user_id))
        if existing_like is None:
            return False
        self._session.delete(existing_like)
        self._session.commit()
        return True

    def count_likes(self, post_id: UUID) -> int:
        """Возвращает количество лайков у поста."""
        stmt = select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
        return int(self._session.scalar(stmt) or 0)

    def count_likes_for_posts(self, post_ids: Sequence[UUID]) -> dict[UUID, int]:
        """Возвращает карту количества лайков для набора постов."""
        if not post_ids:
            return {}
        stmt = (
            select(PostLike.post_id, func.count().label("likes_count"))
            .where(PostLike.post_id.in_(post_ids))
            .group_by(PostLike.post_id)
        )
        rows = self._session.execute(stmt).all()
        return {post_id: int(likes_count) for post_id, likes_count in rows}

    def is_liked(self, post_id: UUID, user_id: UUID) -> bool:
        """Проверяет, поставил ли пользователь лайк посту."""
        return self._session.get(PostLike, (post_id, user_id)) is not None

    def get_liked_post_ids(self, post_ids: Sequence[UUID], user_id: UUID) -> set[UUID]:
        """Возвращает множество идентификаторов постов, лайкнутых пользователем."""
        if not post_ids:
            return set()

        stmt = select(PostLike.post_id).where(
            PostLike.user_id == user_id,
            PostLike.post_id.in_(post_ids),
        )
        rows = self._session.execute(stmt).scalars().all()
        return set(rows)

    def count_posts_by_author(self, author_id: UUID) -> int:
        """Возвращает количество постов автора."""
        stmt = select(func.count()).select_from(Post).where(Post.author_id == author_id)
        return int(self._session.scalar(stmt) or 0)
