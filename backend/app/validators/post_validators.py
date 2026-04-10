"""Валидаторы данных постов."""

from urllib.parse import urlparse


def validate_post_text(text: str) -> None:
    """Проверяет корректность текста поста."""
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("Текст поста не может быть пустым")
    if len(normalized_text) > 5000:
        raise ValueError("Текст поста не должен превышать 5000 символов")


def validate_post_medias(medias: list[str]) -> None:
    """Проверяет корректность списка изображений поста."""
    if len(medias) == 0:
        raise ValueError("Пост должен содержать минимум одно изображение")

    for media in medias:
        parsed = urlparse(media.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Некорректный URL изображения")


def validate_posts_pagination(limit: int, offset: int) -> None:
    """Проверяет корректность параметров пагинации ленты."""
    if limit < 1 or limit > 100:
        raise ValueError("Параметр limit должен быть в диапазоне [1, 100]")
    if offset < 0:
        raise ValueError("Параметр offset не может быть отрицательным")
