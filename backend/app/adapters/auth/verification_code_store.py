"""Redis-адаптер хранения кодов верификации email."""

from __future__ import annotations

import json
from typing import Protocol


class RedisValueClient(Protocol):
    """Минимальный контракт Redis-клиента для записи значений с TTL."""

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        """Сохраняет строковое значение по ключу с TTL."""


class RedisVerificationCodeStore:
    """Хранилище кодов верификации email на базе Redis."""

    def __init__(self, *, redis_client: RedisValueClient) -> None:
        """Инициализирует Redis-клиент хранилища кодов верификации."""
        self.redis_client = redis_client

    async def save_email_verification_code(
        self,
        *,
        email: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        """Сохраняет код верификации и сопутствующие ограничения в Redis."""
        key = f"auth:verify:{email}"
        payload = json.dumps(
            {
                "code": code,
                "attempts_left": max_attempts,
                "resend_cooldown_seconds": resend_cooldown_seconds,
            }
        )
        await self.redis_client.set(key, payload, ex=ttl_seconds)
