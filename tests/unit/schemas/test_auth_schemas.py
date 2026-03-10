from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest
from backend.app.schemas.auth import RegisterRequestSchema, RegisterResponseSchema
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_register_request_normalizes_email_and_accepts_valid_password() -> None:
    valid_password = "valid_pass1!"  # noqa: S105
    payload = RegisterRequestSchema(
        email="  NewUser@Example.COM  ",
        password=valid_password,
    )

    assert str(payload.email) == "NewUser@example.com"
    assert payload.password == valid_password


def test_register_request_rejects_invalid_email() -> None:
    valid_password = "valid_pass1!"  # noqa: S105
    with pytest.raises(ValidationError):
        RegisterRequestSchema(
            email="not-an-email",
            password=valid_password,
        )


def test_register_request_rejects_password_without_digit() -> None:
    no_digit_password = "onlyspecial!"  # noqa: S105
    with pytest.raises(ValidationError):
        RegisterRequestSchema(
            email="user@example.com",
            password=no_digit_password,
        )


@dataclass(slots=True)
class _FakeUser:
    id: UUID
    email: str


def test_register_response_is_built_from_model_attributes() -> None:
    payload = _FakeUser(
        id=UUID("00000000-0000-0000-0000-000000000123"),
        email="newuser@example.com",
    )

    response = RegisterResponseSchema.model_validate(payload)

    assert response.id == UUID("00000000-0000-0000-0000-000000000123")
    assert response.email == "newuser@example.com"
