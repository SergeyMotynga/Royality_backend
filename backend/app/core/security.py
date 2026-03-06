"""Базовые криптографические утилиты для auth-слоя."""

from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16


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
