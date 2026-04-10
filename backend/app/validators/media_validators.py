"""Валидаторы для загружаемых медиа-файлов."""

import re


def validate_image_payload(payload: bytes) -> None:
    """Проверяет, что файл изображения не пустой."""
    if len(payload) == 0:
        raise ValueError("Файл изображения пустой")


def validate_image_content_type(content_type: str | None) -> None:
    """Проверяет, что content-type файла относится к изображению."""
    if content_type is None or not content_type.startswith("image/"):
        raise ValueError("Допускаются только изображения")


def validate_media_tag(tag: str) -> str:
    """Проверяет и нормализует путь-тег для загрузки медиа."""
    normalized_tag = tag.strip()
    if not normalized_tag:
        raise ValueError("Параметр tag не может быть пустым")
    if normalized_tag.startswith("/") or normalized_tag.endswith("/"):
        raise ValueError("Параметр tag не должен начинаться или заканчиваться символом '/'")
    if ".." in normalized_tag or "\\" in normalized_tag:
        raise ValueError("Параметр tag содержит недопустимые символы")
    if re.fullmatch(r"[a-zA-Z0-9/_-]+", normalized_tag) is None:
        raise ValueError("Параметр tag содержит недопустимые символы")
    return normalized_tag
