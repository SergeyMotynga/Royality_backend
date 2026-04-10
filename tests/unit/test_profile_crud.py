"""Unit-тесты CRUD-операций профиля."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base


@pytest.fixture
def db_session() -> Session:
    """Создает изолированную SQLite-сессию для CRUD-тестов профиля."""
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
def test_update_profile_updates_fields(db_session: Session) -> None:
    """Проверяет обновление полей профиля пользователя."""
    user_crud = UserCrud(session=db_session)
    user = user_crud.create_user(login="profile-user", password_hash="hash", name="Старый ник")

    updated = user_crud.update_profile(
        user=user,
        nickname="Новый ник",
        avatar_url="https://example.com/new-avatar.png",
        bio="Обо мне",
        level=14,
    )

    assert updated.name == "Новый ник"
    assert updated.avatar_url == "https://example.com/new-avatar.png"
    assert updated.bio == "Обо мне"
    assert updated.level == 14


@pytest.mark.unit
def test_count_posts_and_followers(db_session: Session) -> None:
    """Проверяет подсчет постов и подписчиков пользователя."""
    user_crud = UserCrud(session=db_session)
    post_crud = PostCrud(session=db_session)
    author = user_crud.create_user(login="author", password_hash="hash", name="Автор")
    follower = user_crud.create_user(login="follower", password_hash="hash", name="Подписчик")
    another_follower = user_crud.create_user(
        login="follower2",
        password_hash="hash",
        name="Подписчик 2",
    )

    post_crud.create_post(
        author_id=author.id,
        text="Пост 1",
        medias=["https://example.com/p1.png"],
        disable_comments=False,
    )
    post_crud.create_post(
        author_id=author.id,
        text="Пост 2",
        medias=["https://example.com/p2.png"],
        disable_comments=False,
    )
    user_crud.add_follower(follower_id=follower.id, followee_id=author.id)
    user_crud.add_follower(follower_id=another_follower.id, followee_id=author.id)

    posts_count = post_crud.count_posts_by_author(author_id=author.id)
    followers_count = user_crud.count_followers(user_id=author.id)

    assert posts_count == 2
    assert followers_count == 2


@pytest.mark.unit
def test_remove_follower_decrements_count(db_session: Session) -> None:
    """Проверяет отписку пользователя и обновление счетчика."""
    user_crud = UserCrud(session=db_session)
    followee = user_crud.create_user(login="target", password_hash="hash", name="Цель")
    follower = user_crud.create_user(
        login="follower-target",
        password_hash="hash",
        name="Подписчик",
    )
    user_crud.add_follower(follower_id=follower.id, followee_id=followee.id)

    removed = user_crud.remove_follower(follower_id=follower.id, followee_id=followee.id)
    followers_count = user_crud.count_followers(user_id=followee.id)

    assert removed is True
    assert followers_count == 0


@pytest.mark.unit
def test_is_following_returns_expected_state(db_session: Session) -> None:
    """Проверяет определение состояния подписки между пользователями."""
    user_crud = UserCrud(session=db_session)
    followee = user_crud.create_user(login="followee", password_hash="hash", name="Цель")
    follower = user_crud.create_user(login="follower-check", password_hash="hash", name="Подписчик")

    assert user_crud.is_following(follower_id=follower.id, followee_id=followee.id) is False

    user_crud.add_follower(follower_id=follower.id, followee_id=followee.id)
    assert user_crud.is_following(follower_id=follower.id, followee_id=followee.id) is True

    user_crud.remove_follower(follower_id=follower.id, followee_id=followee.id)
    assert user_crud.is_following(follower_id=follower.id, followee_id=followee.id) is False
