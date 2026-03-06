"""Собирает корневые endpoint-ы API."""

from fastapi import APIRouter

from backend.app.api.v1.routers import router as v1_router

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router, prefix="/v1")
