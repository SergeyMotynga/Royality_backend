"""CRUD-операции для постов."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.post import Post
from backend.app.models.post_comment import PostComment
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

    def create_comment(self, post_id: UUID, author_id: UUID, text: str) -> PostComment:
        """Создает комментарий к посту и возвращает сохраненную сущность."""
        comment = PostComment(post_id=post_id, author_id=author_id, text=text)
        self._session.add(comment)
        self._session.commit()
        created_comment = self.get_comment_by_id(comment_id=comment.id)
        if created_comment is None:
            raise RuntimeError("Комментарий не удалось загрузить после создания")
        return created_comment

    def get_comment_by_id(self, comment_id: UUID) -> PostComment | None:
        """Возвращает комментарий по идентификатору."""
        stmt = (
            select(PostComment)
            .where(PostComment.id == comment_id)
            .options(
                joinedload(PostComment.author),
                joinedload(PostComment.post),
            )
        )
        return self._session.execute(stmt).scalars().unique().first()

    def list_comments(self, post_id: UUID, limit: int, offset: int) -> list[PostComment]:
        """Возвращает комментарии поста в порядке создания."""
        stmt = (
            select(PostComment)
            .where(PostComment.post_id == post_id)
            .order_by(PostComment.created_at.asc())
            .limit(limit)
            .offset(offset)
            .options(joinedload(PostComment.author))
        )
        return list(self._session.execute(stmt).scalars().unique().all())

    def update_comment(self, comment: PostComment, text: str) -> PostComment:
        """Обновляет текст комментария."""
        comment.text = text
        self._session.add(comment)
        self._session.commit()
        updated_comment = self.get_comment_by_id(comment_id=comment.id)
        if updated_comment is None:
            raise RuntimeError("Комментарий не удалось загрузить после обновления")
        return updated_comment

    def delete_comment(self, comment: PostComment) -> None:
        """Удаляет комментарий."""
        self._session.delete(comment)
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

    def count_comments(self, post_id: UUID) -> int:
        """Возвращает количество комментариев у поста."""
        stmt = select(func.count()).select_from(PostComment).where(PostComment.post_id == post_id)
        return int(self._session.scalar(stmt) or 0)

    def count_comments_for_posts(self, post_ids: Sequence[UUID]) -> dict[UUID, int]:
        """Возвращает карту количества комментариев для набора постов."""
        if not post_ids:
            return {}
        stmt = (
            select(PostComment.post_id, func.count().label("comments_count"))
            .where(PostComment.post_id.in_(post_ids))
            .group_by(PostComment.post_id)
        )
        rows = self._session.execute(stmt).all()
        return {post_id: int(comments_count) for post_id, comments_count in rows}

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
