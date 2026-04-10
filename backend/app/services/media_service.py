"""Сервис загрузки медиа-файлов в MinIO."""

from mimetypes import guess_extension
from urllib.parse import urlparse
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.app.validators.media_validators import (
    validate_image_content_type,
    validate_image_payload,
    validate_media_tag,
)


class MediaUploadError(ValueError):
    """Ошибка загрузки медиа-файла."""


class MediaService:
    """Сервис хранения изображений в S3-совместимом хранилище."""

    def __init__(
        self,
        endpoint: str,
        bucket_name: str,
        region: str,
        secure: bool,
        access_key: str,
        secret_key: str,
        public_endpoint: str | None = None,
        s3_client: object | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._secure = secure
        self._endpoint_url = self._normalize_endpoint(endpoint=endpoint, secure=secure)
        if public_endpoint is None:
            self._public_endpoint_url = self._endpoint_url
        else:
            self._public_endpoint_url = self._normalize_endpoint(
                endpoint=public_endpoint,
                secure=secure,
            )

        self._s3_client = s3_client or boto3.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def upload_post_image(
        self,
        user_id: str,
        file_name: str | None,
        content_type: str | None,
        payload: bytes,
    ) -> str:
        """Загружает изображение поста и возвращает URL объекта."""
        return self.upload_image(
            tag=f"post/{user_id}",
            file_name=file_name,
            content_type=content_type,
            payload=payload,
        )

    def upload_avatar_image(
        self,
        user_id: str,
        file_name: str | None,
        content_type: str | None,
        payload: bytes,
    ) -> str:
        """Загружает аватар пользователя и возвращает URL объекта."""
        return self.upload_image(
            tag=f"profile/{user_id}",
            file_name=file_name,
            content_type=content_type,
            payload=payload,
        )

    def upload_image(
        self,
        tag: str,
        file_name: str | None,
        content_type: str | None,
        payload: bytes,
    ) -> str:
        """Загружает изображение в указанный раздел и возвращает URL объекта."""
        try:
            validate_image_payload(payload=payload)
            validate_image_content_type(content_type=content_type)
            normalized_tag = validate_media_tag(tag=tag)
        except ValueError as exc:
            raise MediaUploadError(str(exc)) from exc

        extension = self._resolve_extension(file_name=file_name, content_type=content_type)
        object_key = f"{normalized_tag}/{uuid4().hex}{extension}"
        try:
            self._s3_client.put_object(  # type: ignore[attr-defined]
                Bucket=self._bucket_name,
                Key=object_key,
                Body=payload,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise MediaUploadError("Не удалось загрузить изображение в хранилище") from exc

        return self._build_public_url(object_key=object_key)

    def _build_public_url(self, object_key: str) -> str:
        """Формирует публичный URL до объекта в бакете."""
        return f"{self._public_endpoint_url}/{self._bucket_name}/{object_key}"

    def _normalize_endpoint(self, endpoint: str, secure: bool) -> str:
        """Нормализует endpoint, добавляя протокол при необходимости."""
        parsed = urlparse(endpoint)
        if parsed.scheme in {"http", "https"}:
            return endpoint.rstrip("/")
        scheme = "https" if secure else "http"
        return f"{scheme}://{endpoint.rstrip('/')}"

    def _resolve_extension(self, file_name: str | None, content_type: str | None) -> str:
        """Определяет расширение загружаемого объекта."""
        if file_name and "." in file_name:
            return f".{file_name.rsplit('.', maxsplit=1)[1].lower()}"

        guessed = guess_extension(content_type or "")
        if guessed:
            return guessed
        return ".bin"
