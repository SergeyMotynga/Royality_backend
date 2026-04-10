"""Публичные endpoint-ы постов."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.app.api.dependencies.auth import CurrentUser, get_current_user
from backend.app.api.dependencies.services import get_post_service
from backend.app.schemas.post import (
    PostAuthorResponse,
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
)
from backend.app.services.post_service import (
    PostNotFoundError,
    PostPermissionError,
    PostResult,
    PostService,
    PostValidationError,
)

router = APIRouter(prefix="/posts", tags=["posts"])


def _build_post_response(post: PostResult) -> PostResponse:
    """Преобразует DTO сервиса в response-схему."""
    return PostResponse(
        id=str(post.id),
        text=post.text,
        medias=post.medias,
        disable_comments=post.disable_comments,
        author=PostAuthorResponse(
            id=str(post.author.id),
            name=post.author.name,
            avatar_url=post.author.avatar_url,
        ),
        likes_count=post.likes_count,
        created_at=post.created_at,
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> PostResponse:
    """Создает новый пост текущего пользователя."""
    try:
        post = service.create_post(
            user_id=current_user.user_id,
            text=payload.text,
            medias=payload.medias,
            disable_comments=payload.disable_comments,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_post_response(post=post)


@router.get("", response_model=list[PostResponse])
def get_feed(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> list[PostResponse]:
    """Возвращает ленту постов всех пользователей."""
    _ = current_user
    try:
        posts = service.get_feed(limit=limit, offset=offset)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [_build_post_response(post=post) for post in posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> PostResponse:
    """Возвращает пост по идентификатору."""
    _ = current_user
    try:
        post = service.get_post(post_id=post_id)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_post_response(post=post)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: str,
    payload: PostUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> PostResponse:
    """Редактирует пост текущего пользователя."""
    try:
        post = service.update_post(
            user_id=current_user.user_id,
            post_id=post_id,
            text=payload.text,
            medias=payload.medias,
            disable_comments=payload.disable_comments,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _build_post_response(post=post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> Response:
    """Удаляет пост текущего пользователя."""
    try:
        service.delete_post(user_id=current_user.user_id, post_id=post_id)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_post(
    post_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> Response:
    """Ставит лайк посту от текущего пользователя."""
    try:
        service.like_post(user_id=current_user.user_id, post_id=post_id)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    post_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> Response:
    """Снимает лайк поста от текущего пользователя."""
    try:
        service.unlike_post(user_id=current_user.user_id, post_id=post_id)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
