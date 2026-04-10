"""Роутер версии API v1."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.admin.health import router as admin_health_router
from backend.app.api.v1.endpoints.public.health import router as public_health_router
from backend.app.api.v1.endpoints.public.posts import router as public_posts_router
from backend.app.api.v1.endpoints.public.users import router as public_users_router

v1_router = APIRouter()
v1_router.include_router(public_health_router)
v1_router.include_router(public_posts_router)
v1_router.include_router(public_users_router)
v1_router.include_router(admin_health_router, prefix="/admin")
