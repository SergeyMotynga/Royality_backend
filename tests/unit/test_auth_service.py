"""Unit-тесты сервиса авторизации."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.core.security import decode_access_token, hash_password
from backend.app.services.auth_service import (
    AuthService,
    AuthValidationError,
    InvalidCredentialsError,
    LoginAlreadyExistsError,
)


@pytest.mark.unit
def test_signup_success(repository_mock_factory) -> None:
    """Проверяет успешную регистрацию пользователя."""
    created_user = SimpleNamespace(
        id=uuid4(),
        login="new-user",
        name="Новый Пользователь",
        created_at=datetime.now(UTC),
    )
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_login": None,
            "create_user": created_user,
        }
    )
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    result = service.signup(login="new-user", password="strong123", name="Новый Пользователь")

    assert result.id == created_user.id
    assert result.login == "new-user"
    assert result.name == "Новый Пользователь"
    user_crud.get_by_login.assert_called_once_with(login="new-user")
    assert user_crud.create_user.call_count == 1


@pytest.mark.unit
def test_signup_duplicate_login(repository_mock_factory) -> None:
    """Проверяет ошибку регистрации с занятым логином."""
    user_crud = repository_mock_factory(sync_methods={"get_by_login": object()})
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    with pytest.raises(LoginAlreadyExistsError):
        service.signup(login="existing", password="strong123", name="Имя")


@pytest.mark.unit
def test_signup_validation_error(repository_mock_factory) -> None:
    """Проверяет ошибку валидации на регистрации."""
    user_crud = repository_mock_factory()
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    with pytest.raises(AuthValidationError):
        service.signup(login="ab", password="123", name="A")


@pytest.mark.unit
def test_login_user_not_found(repository_mock_factory) -> None:
    """Проверяет отказ логина при отсутствии пользователя."""
    user_crud = repository_mock_factory(sync_methods={"get_by_login": None})
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    with pytest.raises(InvalidCredentialsError):
        service.login(login="unknown", password="strong123")


@pytest.mark.unit
def test_login_wrong_password(repository_mock_factory) -> None:
    """Проверяет отказ логина при неверном пароле."""
    stored_user = SimpleNamespace(
        id=uuid4(),
        login="known-user",
        password_hash=hash_password("strong123"),
        is_superuser=False,
    )
    user_crud = repository_mock_factory(sync_methods={"get_by_login": stored_user})
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    with pytest.raises(InvalidCredentialsError):
        service.login(login="known-user", password="wrong-password")


@pytest.mark.unit
def test_login_success(repository_mock_factory) -> None:
    """Проверяет успешный логин и содержимое токена."""
    stored_user = SimpleNamespace(
        id=uuid4(),
        login="known-user",
        password_hash=hash_password("strong123"),
        is_superuser=False,
    )
    user_crud = repository_mock_factory(sync_methods={"get_by_login": stored_user})
    service = AuthService(user_crud=user_crud, secret_key="test-secret-key-32-chars-long-0001")

    token = service.login(login="known-user", password="strong123")
    payload = decode_access_token(token=token, secret_key="test-secret-key-32-chars-long-0001")

    assert payload["sub"] == str(stored_user.id)
    assert payload["login"] == "known-user"
    assert payload["is_superuser"] is False
