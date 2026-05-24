from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest
from backend.app.schemas.auth import (
    RegisterRequestSchema,
    RegisterResponseSchema,
    ResendVerificationCodeRequestSchema,
    ResendVerificationCodeResponseSchema,
    VerifyCodeRequestSchema,
    VerifyCodeResponseSchema,
)
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_register_request_normalizes_phone_number() -> None:
    payload = RegisterRequestSchema(phone_number="8 (999) 123-45-67")

    assert payload.phone_number == "+79991234567"


def test_register_request_rejects_invalid_phone_number() -> None:
    with pytest.raises(ValidationError):
        RegisterRequestSchema(phone_number="123")


@dataclass(slots=True)
class _FakeDispatchResult:
    phone_number: str
    ttl_seconds: int
    resend_cooldown_seconds: int


def test_register_response_is_built_from_model_attributes() -> None:
    payload = _FakeDispatchResult(
        phone_number="+79991234567",
        ttl_seconds=600,
        resend_cooldown_seconds=60,
    )

    response = RegisterResponseSchema.model_validate(payload)

    assert response.phone_number == "+79991234567"
    assert response.ttl_seconds == 600
    assert response.resend_cooldown_seconds == 60


def test_resend_verification_code_request_normalizes_phone_number() -> None:
    payload = ResendVerificationCodeRequestSchema(phone_number="79991234567")

    assert payload.phone_number == "+79991234567"


def test_resend_verification_code_response_is_built_from_model_attributes() -> None:
    payload = _FakeDispatchResult(
        phone_number="+79991234567",
        ttl_seconds=600,
        resend_cooldown_seconds=60,
    )

    response = ResendVerificationCodeResponseSchema.model_validate(payload)

    assert response.phone_number == "+79991234567"
    assert response.ttl_seconds == 600
    assert response.resend_cooldown_seconds == 60


def test_verify_code_request_accepts_numeric_six_digit_code() -> None:
    payload = VerifyCodeRequestSchema(phone_number="8 (999) 123-45-67", code="123456")

    assert payload.phone_number == "+79991234567"
    assert payload.code == "123456"


def test_verify_code_request_rejects_non_numeric_code() -> None:
    with pytest.raises(ValidationError):
        VerifyCodeRequestSchema(phone_number="79991234567", code="12A456")


@dataclass(slots=True)
class _FakeVerifyResponse:
    user_id: UUID
    phone_number: str
    is_new_user: bool


def test_verify_code_response_is_built_from_model_attributes() -> None:
    payload = _FakeVerifyResponse(
        user_id=UUID("00000000-0000-0000-0000-000000000123"),
        phone_number="+79991234567",
        is_new_user=True,
    )

    response = VerifyCodeResponseSchema.model_validate(payload)

    assert response.user_id == UUID("00000000-0000-0000-0000-000000000123")
    assert response.phone_number == "+79991234567"
    assert response.is_new_user is True
