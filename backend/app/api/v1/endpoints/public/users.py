"""Публичные endpoint-ы пользователей."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies.services import get_auth_service
from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from backend.app.services.auth_service import (
    AuthService,
    AuthValidationError,
    InvalidCredentialsError,
    LoginAlreadyExistsError,
)

router = APIRouter(prefix="/users", tags=["users"])


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
