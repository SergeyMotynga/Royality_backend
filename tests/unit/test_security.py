"""Unit-тесты security-утилит."""

import pytest
from jwt import InvalidTokenError

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.mark.unit
def test_hash_password_returns_salt_and_digest() -> None:
    """Проверяет формат сохраненного пароля."""
    result = hash_password("strong-password")
    salt, digest = result.split(":", maxsplit=1)

    assert len(salt) == 32
    assert len(digest) == 64


@pytest.mark.unit
def test_verify_password_success() -> None:
    """Проверяет верификацию корректного пароля."""
    stored = hash_password("strong-password")

    assert verify_password("strong-password", stored) is True


@pytest.mark.unit
def test_verify_password_failure() -> None:
    """Проверяет отказ верификации при неверном пароле."""
    stored = hash_password("strong-password")

    assert verify_password("wrong-password", stored) is False


@pytest.mark.unit
def test_verify_password_for_invalid_hash_format() -> None:
    """Проверяет обработку некорректного формата хеша."""
    assert verify_password("password", "invalid-format") is False


@pytest.mark.unit
def test_create_and_decode_access_token() -> None:
    """Проверяет выпуск и декодирование access token."""
    token = create_access_token(
        secret_key="super-secret-key-32-characters-0001",
        user_id="user-id-1",
        login="user-login",
        is_superuser=True,
    )
    payload = decode_access_token(
        token=token,
        secret_key="super-secret-key-32-characters-0001",
    )

    assert payload["sub"] == "user-id-1"
    assert payload["login"] == "user-login"
    assert payload["is_superuser"] is True


@pytest.mark.unit
def test_decode_access_token_with_invalid_secret() -> None:
    """Проверяет ошибку декодирования при неверном ключе."""
    token = create_access_token(
        secret_key="super-secret-key-32-characters-0001",
        user_id="user-id-1",
        login="user-login",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token=token, secret_key="another-secret-key-32-characters")
