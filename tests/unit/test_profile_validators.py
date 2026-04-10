"""Unit-тесты валидаторов профиля."""

import pytest

from backend.app.validators.profile_validators import (
    validate_profile_avatar_url,
    validate_profile_bio,
    validate_profile_level,
    validate_profile_nickname,
)


@pytest.mark.unit
def test_validate_profile_nickname_success() -> None:
    """Проверяет корректный никнейм профиля."""
    validate_profile_nickname("RoyalityPlayer")


@pytest.mark.unit
def test_validate_profile_nickname_too_short() -> None:
    """Проверяет ошибку слишком короткого никнейма."""
    with pytest.raises(ValueError, match="минимум 2"):
        validate_profile_nickname("A")


@pytest.mark.unit
def test_validate_profile_level_success() -> None:
    """Проверяет корректный уровень профиля."""
    validate_profile_level(10)


@pytest.mark.unit
def test_validate_profile_level_invalid() -> None:
    """Проверяет ошибку некорректного уровня профиля."""
    with pytest.raises(ValueError, match="в диапазоне"):
        validate_profile_level(0)


@pytest.mark.unit
def test_validate_profile_avatar_url_success() -> None:
    """Проверяет корректный URL аватарки."""
    validate_profile_avatar_url("https://example.com/avatar.png")


@pytest.mark.unit
def test_validate_profile_avatar_url_none_success() -> None:
    """Проверяет корректный пустой URL аватарки."""
    validate_profile_avatar_url(None)


@pytest.mark.unit
def test_validate_profile_avatar_url_invalid() -> None:
    """Проверяет ошибку некорректного URL аватарки."""
    with pytest.raises(ValueError, match="Некорректный URL"):
        validate_profile_avatar_url("avatar-local")


@pytest.mark.unit
def test_validate_profile_bio_success() -> None:
    """Проверяет корректное поле 'Обо мне'."""
    validate_profile_bio("Играю в Clash Royale каждый день")


@pytest.mark.unit
def test_validate_profile_bio_too_long() -> None:
    """Проверяет ошибку слишком длинного текста 'Обо мне'."""
    with pytest.raises(ValueError, match="не должен превышать"):
        validate_profile_bio("a" * 1001)
