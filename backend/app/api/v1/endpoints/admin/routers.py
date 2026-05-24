"""Собирает админские endpoint-ы API v1."""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_current_superuser
from backend.app.api.v1.endpoints.admin import health

router = APIRouter(dependencies=[Depends(get_current_superuser)])
router.include_router(health.router)

