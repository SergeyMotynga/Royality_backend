"""Unit-тесты CRUD-слоя постов."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base


@pytest.fixture
def db_session() -> Session:
    """Создает изолированную SQLite-сессию для CRUD-тестов постов."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = local_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.unit
def test_create_post_and_get_by_id(db_session: Session) -> None:
    """Проверяет создание поста и получение по идентификатору."""
    user_crud = UserCrud(session=db_session)
    post_crud = PostCrud(session=db_session)
    user = user_crud.create_user(login="post-author", password_hash="hash", name="Автор")

    created_post = post_crud.create_post(
        author_id=user.id,
        text="Текст поста",
        medias=["https://example.com/post.jpg"],
        disable_comments=False,
    )
    found_post = post_crud.get_post_by_id(post_id=created_post.id)

    assert found_post is not None
    assert found_post.text == "Текст поста"
    assert [media.url for media in found_post.medias] == ["https://example.com/post.jpg"]
    assert found_post.author.name == "Автор"


@pytest.mark.unit
def test_update_post_replaces_media(db_session: Session) -> None:
    """Проверяет обновление текста, флага и медиа поста."""
    user_crud = UserCrud(session=db_session)
    post_crud = PostCrud(session=db_session)
    user = user_crud.create_user(login="post-editor", password_hash="hash", name="Редактор")
    post = post_crud.create_post(
        author_id=user.id,
        text="Старый текст",
        medias=["https://example.com/old.jpg"],
        disable_comments=False,
    )

    updated_post = post_crud.update_post(
        post=post,
        text="Новый текст",
        medias=["https://example.com/new.jpg"],
        disable_comments=True,
    )

    assert updated_post.text == "Новый текст"
    assert updated_post.disable_comments is True
    assert [media.url for media in updated_post.medias] == ["https://example.com/new.jpg"]


@pytest.mark.unit
def test_like_and_unlike_flow(db_session: Session) -> None:
    """Проверяет жизненный цикл лайка поста."""
    user_crud = UserCrud(session=db_session)
    post_crud = PostCrud(session=db_session)
    author = user_crud.create_user(login="post-likes-author", password_hash="hash", name="Автор")
    liker = user_crud.create_user(login="post-likes-user", password_hash="hash", name="Лайкер")
    post = post_crud.create_post(
        author_id=author.id,
        text="Пост для лайка",
        medias=["https://example.com/like.jpg"],
        disable_comments=False,
    )

    created_like = post_crud.add_like(post_id=post.id, user_id=liker.id)
    repeated_like = post_crud.add_like(post_id=post.id, user_id=liker.id)
    likes_count = post_crud.count_likes(post_id=post.id)
    removed_like = post_crud.remove_like(post_id=post.id, user_id=liker.id)
    likes_count_after_remove = post_crud.count_likes(post_id=post.id)

    assert created_like is True
    assert repeated_like is False
    assert likes_count == 1
    assert removed_like is True
    assert likes_count_after_remove == 0


@pytest.mark.unit
def test_list_feed_and_delete_post(db_session: Session) -> None:
    """Проверяет получение ленты и удаление поста."""
    user_crud = UserCrud(session=db_session)
    post_crud = PostCrud(session=db_session)
    author = user_crud.create_user(login="post-feed", password_hash="hash", name="Автор")

    first_post = post_crud.create_post(
        author_id=author.id,
        text="Первый пост",
        medias=["https://example.com/first.jpg"],
        disable_comments=False,
    )
    second_post = post_crud.create_post(
        author_id=author.id,
        text="Второй пост",
        medias=["https://example.com/second.jpg"],
        disable_comments=False,
    )

    feed = post_crud.list_feed(limit=10, offset=0)
    post_crud.delete_post(post=first_post)
    deleted_post = post_crud.get_post_by_id(post_id=first_post.id)
    existing_post = post_crud.get_post_by_id(post_id=second_post.id)

    assert len(feed) == 2
    assert deleted_post is None
    assert existing_post is not None
