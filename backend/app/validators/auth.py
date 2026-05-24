"""Бизнес-валидаторы auth-сценариев."""

from __future__ import annotations

import re

from backend.app.core.exceptions import InvalidPhoneNumberError

PHONE_NUMBER_PATTERN = re.compile(r"^\+[1-9]\d{10,14}$")


def normalize_phone_number(phone_number: str) -> str:
    """Нормализует номер телефона и проверяет допустимый формат."""
    compact = re.sub(r"[^\d+]", "", phone_number.strip())

    if compact.startswith("+"):
        digits = re.sub(r"\D", "", compact)
        normalized = f"+{digits}"
    else:
        digits = re.sub(r"\D", "", compact)
        if len(digits) == 11 and digits.startswith("8"):
            normalized = f"+7{digits[1:]}"
        elif len(digits) == 11 and digits.startswith("7"):
            normalized = f"+{digits}"
        elif len(digits) == 10:
            normalized = f"+7{digits}"
        else:
            normalized = f"+{digits}"

    if not PHONE_NUMBER_PATTERN.fullmatch(normalized):
        raise InvalidPhoneNumberError()

    return normalized
