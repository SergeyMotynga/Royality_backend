"""Утилиты безопасности для паролей и токенов."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime

import jwt


def hash_password(password: str) -> str:
    """Строит salted-хеш пароля для хранения в БД."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"{salt}:{digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверяет соответствие пароля сохраненному salted-хешу."""
    try:
        salt, digest = stored_hash.split(":", maxsplit=1)
    except ValueError:
        return False
    current_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return hmac.compare_digest(current_digest, digest)


def create_access_token(
    secret_key: str,
    user_id: str,
    login: str,
    is_superuser: bool = False,
) -> str:
    """Создает бессрочный access token."""
    payload = {
        "sub": user_id,
        "login": login,
        "is_superuser": is_superuser,
        "iat": int(datetime.now(UTC).timestamp()),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict:
    """Декодирует access token и возвращает payload."""
    return jwt.decode(token, secret_key, algorithms=["HS256"])
