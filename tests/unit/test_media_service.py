"""Unit-тесты сервиса загрузки медиа."""

from urllib.parse import urlparse

import pytest

from backend.app.services.media_service import MediaService, MediaUploadError


class FakeS3Client:
    """Простой фейк S3-клиента для проверок вызовов upload."""

    def __init__(self) -> None:
        self.put_object_calls: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> None:
        """Фиксирует вызов put_object."""
        self.put_object_calls.append(kwargs)


@pytest.mark.unit
def test_upload_post_image_success() -> None:
    """Проверяет успешную загрузку изображения поста."""
    client = FakeS3Client()
    service = MediaService(
        endpoint="localhost:9000",
        bucket_name="royality-media",
        region="us-east-1",
        secure=False,
        access_key="minio-user",
        secret_key="minio-password",
        public_endpoint="localhost:9000",
        s3_client=client,
    )

    url = service.upload_post_image(
        user_id="user-1",
        file_name="photo.jpg",
        content_type="image/jpeg",
        payload=b"binary-image-content",
    )

    assert len(client.put_object_calls) == 1
    call = client.put_object_calls[0]
    assert call["Bucket"] == "royality-media"
    assert call["ContentType"] == "image/jpeg"
    assert isinstance(call["Body"], bytes)

    parsed = urlparse(url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "localhost:9000"
    assert parsed.path.startswith("/royality-media/post/user-1/")
    assert parsed.path.endswith(".jpg")


@pytest.mark.unit
def test_upload_post_image_invalid_content_type() -> None:
    """Проверяет ошибку для неподдерживаемого типа файла."""
    service = MediaService(
        endpoint="localhost:9000",
        bucket_name="royality-media",
        region="us-east-1",
        secure=False,
        access_key="minio-user",
        secret_key="minio-password",
        public_endpoint="localhost:9000",
        s3_client=FakeS3Client(),
    )

    with pytest.raises(MediaUploadError, match="Допускаются только изображения"):
        service.upload_post_image(
            user_id="user-1",
            file_name="notes.txt",
            content_type="text/plain",
            payload=b"text-content",
        )


@pytest.mark.unit
def test_upload_post_image_empty_payload() -> None:
    """Проверяет ошибку для пустого файла."""
    service = MediaService(
        endpoint="localhost:9000",
        bucket_name="royality-media",
        region="us-east-1",
        secure=False,
        access_key="minio-user",
        secret_key="minio-password",
        public_endpoint="localhost:9000",
        s3_client=FakeS3Client(),
    )

    with pytest.raises(MediaUploadError, match="Файл изображения пустой"):
        service.upload_post_image(
            user_id="user-1",
            file_name="photo.jpg",
            content_type="image/jpeg",
            payload=b"",
        )
