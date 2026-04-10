"""Валидаторы профиля пользователя."""

from urllib.parse import urlparse


def validate_profile_nickname(nickname: str) -> None:
    """Проверяет корректность никнейма профиля."""
    normalized_nickname = nickname.strip()
    if len(normalized_nickname) < 2:
        raise ValueError("Никнейм должен содержать минимум 2 символа")
    if len(normalized_nickname) > 128:
        raise ValueError("Никнейм не должен превышать 128 символов")


def validate_profile_level(level: int) -> None:
    """Проверяет корректность уровня пользователя."""
    if level < 1 or level > 100:
        raise ValueError("Уровень профиля должен быть в диапазоне [1, 100]")


def validate_profile_avatar_url(avatar_url: str | None) -> None:
    """Проверяет корректность URL аватарки профиля."""
    if avatar_url is None:
        return

    parsed = urlparse(avatar_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Некорректный URL аватарки")


def validate_profile_bio(bio: str | None) -> None:
    """Проверяет корректность текста 'Обо мне'."""
    if bio is None:
        return

    if len(bio) > 1000:
        raise ValueError("Текст 'Обо мне' не должен превышать 1000 символов")
