"""Unit-тесты валидаторов авторизации."""

import pytest

from backend.app.validators.auth_validators import validate_login, validate_name, validate_password


@pytest.mark.unit
def test_validate_login_success() -> None:
    """Проверяет корректный логин."""
    validate_login("valid_login")


@pytest.mark.unit
def test_validate_login_too_short() -> None:
    """Проверяет ошибку слишком короткого логина."""
    with pytest.raises(ValueError, match="минимум 3"):
        validate_login("ab")


@pytest.mark.unit
def test_validate_login_with_spaces() -> None:
    """Проверяет ошибку логина с пробелами."""
    with pytest.raises(ValueError, match="пробелы"):
        validate_login("user name")


@pytest.mark.unit
def test_validate_password_success() -> None:
    """Проверяет корректный пароль."""
    validate_password("strong123")


@pytest.mark.unit
def test_validate_password_too_short() -> None:
    """Проверяет ошибку слишком короткого пароля."""
    with pytest.raises(ValueError, match="минимум 8"):
        validate_password("1234567")


@pytest.mark.unit
def test_validate_name_success() -> None:
    """Проверяет корректное имя."""
    validate_name("Иван")


@pytest.mark.unit
def test_validate_name_too_short() -> None:
    """Проверяет ошибку слишком короткого имени."""
    with pytest.raises(ValueError, match="минимум 2"):
        validate_name("A")
