"""Собирает публичные endpoint-ы API v1."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.public import auth, health

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
