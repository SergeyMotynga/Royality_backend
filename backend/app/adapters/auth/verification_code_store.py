"""Redis-адаптер хранения OTP-кодов подтверждения телефона."""

from __future__ import annotations

import json
import time
from typing import Protocol

from backend.app.adapters.auth.constants import build_auth_code_key
from backend.app.services.auth.contracts import AuthCodeState


class RedisValueClient(Protocol):
    """Минимальный контракт Redis-клиента для записи/чтения значений."""

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        """Сохраняет строковое значение по ключу с TTL."""

    async def get(self, key: str) -> str | None:
        """Возвращает строковое значение по ключу либо None."""

    async def delete(self, key: str) -> int:
        """Удаляет значение по ключу и возвращает число удаленных записей."""


class RedisVerificationCodeStore:
    """Хранилище OTP-кодов подтверждения телефона на базе Redis."""

    def __init__(self, *, redis_client: RedisValueClient) -> None:
        """Инициализирует Redis-клиент хранилища кодов."""
        self.redis_client = redis_client

    async def save_auth_code(
        self,
        *,
        phone_number: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        """Сохраняет OTP-код и сопутствующие ограничения в Redis."""
        now = int(time.time())
        state = AuthCodeState(
            code=code,
            attempts_left=max_attempts,
            resend_available_at=now + resend_cooldown_seconds,
            expires_at=now + ttl_seconds,
        )
        await self._save_state(phone_number=phone_number, state=state)

    async def get_auth_code(self, *, phone_number: str) -> AuthCodeState | None:
        """Возвращает текущее состояние OTP-кода для номера телефона."""
        key = build_auth_code_key(phone_number)
        raw_payload = await self.redis_client.get(key)
        if raw_payload is None:
            return None

        payload = json.loads(raw_payload)
        return AuthCodeState(
            code=str(payload["code"]),
            attempts_left=int(payload["attempts_left"]),
            resend_available_at=int(payload["resend_available_at"]),
            expires_at=int(payload["expires_at"]),
        )

    async def update_auth_code(
        self,
        *,
        phone_number: str,
        state: AuthCodeState,
    ) -> None:
        """Обновляет состояние OTP-кода с сохранением оставшегося TTL."""
        await self._save_state(phone_number=phone_number, state=state)

    async def delete_auth_code(self, *, phone_number: str) -> None:
        """Удаляет OTP-код для номера телефона."""
        key = build_auth_code_key(phone_number)
        await self.redis_client.delete(key)

    async def _save_state(self, *, phone_number: str, state: AuthCodeState) -> None:
        """Сохраняет состояние OTP-кода с корректным TTL."""
        key = build_auth_code_key(phone_number)
        now = int(time.time())
        ttl_seconds = max(1, state.expires_at - now)
        payload = json.dumps(
            {
                "code": state.code,
                "attempts_left": state.attempts_left,
                "resend_available_at": state.resend_available_at,
                "expires_at": state.expires_at,
            }
        )
        await self.redis_client.set(key, payload, ex=ttl_seconds)
