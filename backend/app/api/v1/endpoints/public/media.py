"""Публичный endpoint загрузки медиа."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from backend.app.api.dependencies.auth import CurrentUser, get_current_user
from backend.app.api.dependencies.services import get_media_service
from backend.app.schemas.media import MediaUploadResponse
from backend.app.services.media_service import MediaService, MediaUploadError

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    tag: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
) -> MediaUploadResponse:
    """Загружает изображение и возвращает URL в MinIO."""
    _ = current_user
    payload = await file.read()
    try:
        url = media_service.upload_image(
            tag=tag,
            file_name=file.filename,
            content_type=file.content_type,
            payload=payload,
        )
    except MediaUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MediaUploadResponse(url=url)
