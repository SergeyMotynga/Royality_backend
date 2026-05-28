"""Публичные endpoint-ы постов."""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)

from backend.app.api.dependencies.auth import CurrentUser, get_current_user
from backend.app.api.dependencies.services import get_media_service, get_post_service
from backend.app.schemas.post import (
    PostCommentCreateRequest,
    PostCommentResponse,
    PostCommentUpdateRequest,
    PostAuthorResponse,
    PostResponse,
    PostUpdateRequest,
)
from backend.app.services.media_service import MediaService, MediaUploadError
from backend.app.services.post_service import (
    PostCommentsDisabledError,
    PostCommentResult,
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
        comments_count=post.comments_count,
        is_liked=post.is_liked,
        created_at=post.created_at,
    )


def _build_comment_response(comment: PostCommentResult) -> PostCommentResponse:
    """Преобразует DTO комментария в response-схему."""
    return PostCommentResponse(
        id=str(comment.id),
        post_id=str(comment.post_id),
        text=comment.text,
        author=PostAuthorResponse(
            id=str(comment.author.id),
            name=comment.author.name,
            avatar_url=comment.author.avatar_url,
        ),
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    text: str = Form(...),
    image: UploadFile | None = File(default=None),
    disable_comments: bool = Form(default=False),
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
    media_service: MediaService = Depends(get_media_service),
) -> PostResponse:
    """Создает новый пост текущего пользователя."""
    try:
        medias: list[str] = []
        if image is not None:
            image_payload = await image.read()
            media_url = media_service.upload_post_image(
                user_id=current_user.user_id,
                file_name=image.filename,
                content_type=image.content_type,
                payload=image_payload,
            )
            medias = [media_url]
        post = service.create_post(
            user_id=current_user.user_id,
            text=text,
            medias=medias,
            disable_comments=disable_comments,
        )
    except MediaUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
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
    try:
        posts = service.get_feed(
            limit=limit,
            offset=offset,
            viewer_user_id=current_user.user_id,
        )
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
    try:
        post = service.get_post(
            post_id=post_id,
            viewer_user_id=current_user.user_id,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_post_response(post=post)


@router.get("/{post_id}/comments", response_model=list[PostCommentResponse])
def list_comments(
    post_id: str,
    limit: int = Query(default=50),
    offset: int = Query(default=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> list[PostCommentResponse]:
    """Возвращает комментарии поста."""
    try:
        comments = service.list_comments(post_id=post_id, limit=limit, offset=offset)
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_build_comment_response(comment=comment) for comment in comments]


@router.post(
    "/{post_id}/comments",
    response_model=PostCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: str,
    payload: PostCommentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> PostCommentResponse:
    """Создает комментарий текущего пользователя к посту."""
    try:
        comment = service.create_comment(
            user_id=current_user.user_id,
            post_id=post_id,
            text=payload.text,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostCommentsDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_comment_response(comment=comment)


@router.put("/{post_id}/comments/{comment_id}", response_model=PostCommentResponse)
def update_comment(
    post_id: str,
    comment_id: str,
    payload: PostCommentUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> PostCommentResponse:
    """Редактирует комментарий текущего пользователя."""
    try:
        comment = service.update_comment(
            user_id=current_user.user_id,
            post_id=post_id,
            comment_id=comment_id,
            text=payload.text,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _build_comment_response(comment=comment)


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    post_id: str,
    comment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
) -> Response:
    """Удаляет комментарий текущего пользователя."""
    try:
        service.delete_comment(
            user_id=current_user.user_id,
            post_id=post_id,
            comment_id=comment_id,
        )
    except PostValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
