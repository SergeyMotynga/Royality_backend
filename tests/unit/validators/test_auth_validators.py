from __future__ import annotations

import pytest
from backend.app.core.exceptions import InvalidPhoneNumberError
from backend.app.validators.auth import normalize_phone_number

pytestmark = pytest.mark.unit


def test_normalize_phone_number_transforms_local_number_to_e164() -> None:
    normalized = normalize_phone_number("8 (999) 123-45-67")

    assert normalized == "+79991234567"


def test_normalize_phone_number_accepts_number_without_plus_sign() -> None:
    normalized = normalize_phone_number("79991234567")

    assert normalized == "+79991234567"


def test_normalize_phone_number_raises_for_invalid_value() -> None:
    with pytest.raises(InvalidPhoneNumberError):
        normalize_phone_number("123")
