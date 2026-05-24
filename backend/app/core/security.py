"""Базовые криптографические утилиты для auth-слоя."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from backend.app.core.exceptions import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    WeakPasswordError,
)

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
DEFAULT_PASSWORD_MIN_LENGTH = 8
DEFAULT_PASSWORD_MAX_LENGTH = 26


@dataclass(slots=True)
class AccessTokenPayload:
    """Данные access-токена после валидации подписи и срока действия."""

    user_id: UUID
    session_id: UUID
    expires_at: datetime


def hash_password(password: str) -> str:
    """Хэширует пароль через PBKDF2 и возвращает строку для хранения."""
    salt = secrets.token_bytes(SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Проверяет пароль по сохраненному PBKDF2-хэшу."""
    try:
        algorithm_part, iterations_part, salt_hex, hash_hex = encoded_hash.split("$", maxsplit=3)
        algorithm = algorithm_part.removeprefix("pbkdf2_")
        iterations = int(iterations_part)
    except (TypeError, ValueError):
        return False

    expected_hash = hashlib.pbkdf2_hmac(
        algorithm,
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    )
    return hmac.compare_digest(expected_hash.hex(), hash_hex)


def hash_token(token: str) -> str:
    """Хэширует токен для хранения в БД без сохранения исходного значения."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    """Генерирует случайный refresh-токен."""
    return secrets.token_urlsafe(48)


def create_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    secret_key: str,
    expires_in_minutes: int,
    now: datetime | None = None,
) -> str:
    """Создает подписанный access-токен."""
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=expires_in_minutes)

    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "exp": int(expires_at.timestamp()),
        "typ": "access",
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _base64url_encode(payload_json)
    signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    signature_part = _base64url_encode(signature)
    return f"{payload_part}.{signature_part}"


def parse_access_token(
    *,
    token: str,
    secret_key: str,
    now: datetime | None = None,
) -> AccessTokenPayload:
    """Проверяет подпись и срок действия access-токена."""
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
    except ValueError as error:
        raise InvalidAccessTokenError() from error

    expected_signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual_signature = _base64url_decode(signature_part)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise InvalidAccessTokenError()

    payload_raw = _base64url_decode(payload_part)
    try:
        payload = json.loads(payload_raw.decode("utf-8"))
        user_id = UUID(str(payload["sub"]))
        session_id = UUID(str(payload["sid"]))
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
        token_type = str(payload["typ"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise InvalidAccessTokenError() from error

    if token_type != "access":
        raise InvalidAccessTokenError()

    current_time = now or datetime.now(UTC)
    if expires_at <= current_time:
        raise AccessTokenExpiredError()

    return AccessTokenPayload(
        user_id=user_id,
        session_id=session_id,
        expires_at=expires_at,
    )


def validate_password_policy(
    password: str,
    *,
    min_length: int = DEFAULT_PASSWORD_MIN_LENGTH,
    max_length: int = DEFAULT_PASSWORD_MAX_LENGTH,
) -> None:
    """Проверяет пароль по базовой политике и выбрасывает ошибку при нарушении."""
    if len(password) < min_length:
        raise WeakPasswordError.too_short(min_length=min_length)

    if len(password) > max_length:
        raise WeakPasswordError.too_long(max_length=max_length)

    if any(character.isspace() for character in password):
        raise WeakPasswordError.contains_whitespace()

    if not any(character.isdigit() for character in password):
        raise WeakPasswordError.missing_digit()

    if not any((not character.isalnum()) and (not character.isspace()) for character in password):
        raise WeakPasswordError.missing_special_symbol()


def _base64url_encode(raw: bytes) -> str:
    """Кодирует bytes в base64url без завершающих символов '='."""
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64url_decode(encoded: str) -> bytes:
    """Декодирует base64url-строку с восстановлением выравнивания."""
    padding = "=" * (-len(encoded) % 4)
    try:
        return base64.urlsafe_b64decode(encoded + padding)
    except (ValueError, binascii.Error) as error:
        raise InvalidAccessTokenError() from error
