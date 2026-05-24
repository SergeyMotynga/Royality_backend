"""Pydantic-схемы API-контрактов."""

from backend.app.schemas.auth import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    ResendVerificationCodeRequestSchema,
    ResendVerificationCodeResponseSchema,
    VerifyCodeRequestSchema,
    VerifyCodeResponseSchema,
)

__all__ = [
    "RegisterRequestSchema",
    "RegisterResponseSchema",
    "ResendVerificationCodeRequestSchema",
    "ResendVerificationCodeResponseSchema",
    "VerifyCodeRequestSchema",
    "VerifyCodeResponseSchema",
]

