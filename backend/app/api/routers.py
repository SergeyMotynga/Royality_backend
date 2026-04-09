"""Корневой API-роутер."""

from fastapi import APIRouter

from backend.app.api.v1.routers import v1_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/api/v1")
