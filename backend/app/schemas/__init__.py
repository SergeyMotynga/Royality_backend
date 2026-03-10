"""Pydantic-схемы API-контрактов."""

from backend.app.schemas.auth import RegisterRequestSchema, RegisterResponseSchema

__all__ = [
    "RegisterRequestSchema",
    "RegisterResponseSchema",
]
