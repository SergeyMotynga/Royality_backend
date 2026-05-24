"""Админские endpoint-ы для управления пользователями."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.api.deps import get_auth_service
from backend.app.schemas.auth import (
    SuperuserCreateRequestSchema,
    SuperuserCreateResponseSchema,
)
from backend.app.services.auth import AuthService

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.post(
    "/superusers",
    status_code=status.HTTP_201_CREATED,
    response_model=SuperuserCreateResponseSchema,
)
async def create_superuser(
    payload: SuperuserCreateRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuperuserCreateResponseSchema:
    """Создает superuser из админского контура без email-верификации."""
    created_user = await auth_service.create_superuser(
        email=str(payload.email),
        password=payload.password,
    )
    return SuperuserCreateResponseSchema.model_validate(created_user)
