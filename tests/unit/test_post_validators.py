"""Unit-тесты валидаторов постов."""

import pytest

from backend.app.validators.post_validators import (
    validate_post_medias,
    validate_post_text,
    validate_posts_pagination,
)


@pytest.mark.unit
def test_validate_post_text_success() -> None:
    """Проверяет корректный текст поста."""
    validate_post_text("Это корректный текст поста")


@pytest.mark.unit
def test_validate_post_text_empty() -> None:
    """Проверяет ошибку пустого текста поста."""
    with pytest.raises(ValueError, match="не может быть пустым"):
        validate_post_text("   ")


@pytest.mark.unit
def test_validate_post_medias_success() -> None:
    """Проверяет корректный список медиа поста."""
    validate_post_medias(["https://example.com/image.jpg"])


@pytest.mark.unit
def test_validate_post_medias_empty() -> None:
    """Проверяет ошибку пустого списка медиа."""
    with pytest.raises(ValueError, match="минимум одно изображение"):
        validate_post_medias([])


@pytest.mark.unit
def test_validate_post_medias_invalid_url() -> None:
    """Проверяет ошибку некорректного URL изображения."""
    with pytest.raises(ValueError, match="Некорректный URL"):
        validate_post_medias(["not-a-url"])


@pytest.mark.unit
def test_validate_posts_pagination_success() -> None:
    """Проверяет корректные параметры пагинации."""
    validate_posts_pagination(limit=20, offset=0)


@pytest.mark.unit
def test_validate_posts_pagination_invalid_limit() -> None:
    """Проверяет ошибку некорректного лимита."""
    with pytest.raises(ValueError, match="должен быть в диапазоне"):
        validate_posts_pagination(limit=0, offset=0)


@pytest.mark.unit
def test_validate_posts_pagination_invalid_offset() -> None:
    """Проверяет ошибку некорректного сдвига."""
    with pytest.raises(ValueError, match="не может быть отрицательным"):
        validate_posts_pagination(limit=20, offset=-1)
