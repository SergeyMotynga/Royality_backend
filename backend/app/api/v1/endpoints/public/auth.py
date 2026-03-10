"""Публичные auth-endpoint-ы API v1."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from backend.app.api.deps import get_auth_service
from backend.app.schemas.auth import RegisterRequestSchema, RegisterResponseSchema
from backend.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_ip(request: Request) -> str | None:
    """Возвращает IP клиента с учетом прокси-заголовков."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    if request.client is None:
        return None
    return request.client.host


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponseSchema,
)
async def register(
    payload: RegisterRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> RegisterResponseSchema:
    """Регистрирует пользователя по email/паролю и запускает email-верификацию."""
    created_user = await auth_service.register(
        email=str(payload.email),
        password=payload.password,
        ip_address=client_ip,
    )
    return RegisterResponseSchema.model_validate(created_user)
