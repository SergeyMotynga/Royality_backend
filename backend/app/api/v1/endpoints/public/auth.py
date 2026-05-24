"""Публичные auth-endpoint-ы API v1."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from backend.app.api.deps import get_auth_service
from backend.app.schemas.auth import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    ResendVerificationCodeRequestSchema,
    ResendVerificationCodeResponseSchema,
    VerifyCodeRequestSchema,
    VerifyCodeResponseSchema,
)
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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RegisterResponseSchema,
)
async def register(
    payload: RegisterRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> RegisterResponseSchema:
    """Запрашивает OTP-код подтверждения для номера телефона."""
    dispatch_result = await auth_service.register(
        phone_number=payload.phone_number,
        ip_address=client_ip,
    )
    return RegisterResponseSchema.model_validate(dispatch_result)


@router.post(
    "/verify-code",
    status_code=status.HTTP_200_OK,
    response_model=VerifyCodeResponseSchema,
)
async def verify_code(
    payload: VerifyCodeRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> VerifyCodeResponseSchema:
    """Подтверждает OTP-код и выполняет вход/регистрацию пользователя."""
    verify_result = await auth_service.verify_code(
        phone_number=payload.phone_number,
        code=payload.code,
    )
    return VerifyCodeResponseSchema(
        user_id=verify_result.user.id,
        phone_number=verify_result.user.phone_number,
        is_new_user=verify_result.is_new_user,
    )


@router.post(
    "/resend-verification-code",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ResendVerificationCodeResponseSchema,
)
async def resend_verification_code(
    payload: ResendVerificationCodeRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> ResendVerificationCodeResponseSchema:
    """Переотправляет OTP-код подтверждения номера телефона."""
    dispatch_result = await auth_service.resend_verification_code(
        phone_number=payload.phone_number,
        ip_address=client_ip,
    )
    return ResendVerificationCodeResponseSchema.model_validate(dispatch_result)

