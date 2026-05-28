"""Публичные endpoint-ы пользователей."""

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from backend.app.api.dependencies.auth import CurrentUser, get_current_user
from backend.app.api.dependencies.services import (
    get_auth_service,
    get_media_service,
    get_profile_service,
    get_push_notification_service,
)
from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from backend.app.schemas.media import MediaUploadResponse
from backend.app.schemas.profile import UserProfileResponse, UserProfileUpdateRequest
from backend.app.schemas.push import PushTokenRequest
from backend.app.services.auth_service import (
    AuthService,
    AuthValidationError,
    InvalidCredentialsError,
    LoginAlreadyExistsError,
)
from backend.app.services.media_service import MediaService, MediaUploadError
from backend.app.services.profile_service import (
    ProfileNotFoundError,
    ProfileResult,
    ProfileService,
    ProfileValidationError,
)
from backend.app.services.push_notification_service import (
    PushNotFoundError,
    PushNotificationService,
    PushValidationError,
)

router = APIRouter(prefix="/users", tags=["users"])


def _build_profile_response(profile: ProfileResult) -> UserProfileResponse:
    """Преобразует DTO профиля в response-схему."""
    return UserProfileResponse(
        id=str(profile.id),
        nickname=profile.nickname,
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        level=profile.level,
        posts_count=profile.posts_count,
        followers_count=profile.followers_count,
        is_following=profile.is_following,
        created_at=profile.created_at,
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    service: AuthService = Depends(get_auth_service),
) -> SignupResponse:
    """Регистрирует пользователя."""
    try:
        result = service.signup(login=payload.login, password=payload.password, name=payload.name)
    except AuthValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LoginAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SignupResponse(
        id=str(result.id),
        login=result.login,
        name=result.name,
        created_at=result.created_at,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    """Авторизует пользователя и возвращает access token."""
    try:
        token = service.login(login=payload.login, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return LoginResponse(access_token=token)


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    """Обновляет профиль текущего пользователя."""
    try:
        profile = service.update_my_profile(
            current_user_id=current_user.user_id,
            nickname=payload.nickname,
            avatar_url=payload.avatar_url,
            bio=payload.bio,
            level=payload.level,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_profile_response(profile=profile)


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    """Возвращает профиль текущего пользователя."""
    try:
        profile = service.get_profile(
            user_id=current_user.user_id,
            viewer_user_id=current_user.user_id,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_profile_response(profile=profile)


@router.post("/me/avatar", response_model=MediaUploadResponse)
async def upload_my_avatar(
    image: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> MediaUploadResponse:
    """Загружает аватар текущего пользователя и возвращает публичный URL."""
    payload = await image.read()
    try:
        url = media_service.upload_avatar_image(
            user_id=current_user.user_id,
            file_name=image.filename,
            content_type=image.content_type,
            payload=payload,
        )
        profile_service.update_my_avatar(
            current_user_id=current_user.user_id,
            avatar_url=url,
        )
    except MediaUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MediaUploadResponse(url=url)


@router.put("/me/push-token", status_code=status.HTTP_204_NO_CONTENT)
def register_my_push_token(
    payload: PushTokenRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PushNotificationService = Depends(get_push_notification_service),
) -> Response:
    """Регистрирует FCM-токен устройства текущего пользователя."""
    try:
        service.register_token(
            user_id=current_user.user_id,
            token=payload.token,
            platform=payload.platform,
            device_id=payload.device_id,
        )
    except PushValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PushNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/push-token", status_code=status.HTTP_204_NO_CONTENT)
def unregister_my_push_token(
    payload: PushTokenRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PushNotificationService = Depends(get_push_notification_service),
) -> Response:
    """Удаляет FCM-токен устройства текущего пользователя."""
    try:
        service.unregister_token(user_id=current_user.user_id, token=payload.token)
    except PushValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    """Подписывает текущего пользователя на пользователя по идентификатору."""
    try:
        service.follow_user(current_user_id=current_user.user_id, target_user_id=user_id)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    """Отписывает текущего пользователя от пользователя по идентификатору."""
    try:
        service.unfollow_user(current_user_id=current_user.user_id, target_user_id=user_id)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_profile(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    """Возвращает профиль пользователя по идентификатору."""
    try:
        profile = service.get_profile(
            user_id=user_id,
            viewer_user_id=current_user.user_id,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _build_profile_response(profile=profile)
