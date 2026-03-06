"""Собирает endpoint-ы API v1."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.admin.routers import router as admin_router
from backend.app.api.v1.endpoints.public.routers import router as public_router

router = APIRouter()
router.include_router(public_router)
router.include_router(admin_router, prefix="/admin")
