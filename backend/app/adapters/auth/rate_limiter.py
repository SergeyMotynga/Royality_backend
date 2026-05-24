"""Redis-адаптер проверки лимитов auth-запросов."""

from __future__ import annotations

from typing import Protocol

from backend.app.adapters.auth.constants import build_auth_ip_key, build_auth_phone_key
from backend.app.core.config import Settings
from backend.app.core.exceptions import RateLimitExceededError


class RedisCounterClient(Protocol):
    """Минимальный контракт Redis-клиента для счетчиков rate-limit."""

    async def incr(self, key: str) -> int:
        """Увеличивает счетчик ключа и возвращает новое значение."""

    async def expire(self, key: str, ttl_seconds: int) -> None:
        """Устанавливает TTL для ключа счетчика."""


class RedisAuthRateLimiter:
    """Rate-limit auth-запросов по номеру телефона и IP через Redis-счетчики."""

    def __init__(
        self,
        *,
        redis_client: RedisCounterClient,
        max_requests_per_phone: int,
        max_requests_per_ip: int,
        window_seconds: int,
    ) -> None:
        """Инициализирует параметры лимитов и Redis-клиент."""
        self.redis_client = redis_client
        self.max_requests_per_phone = max_requests_per_phone
        self.max_requests_per_ip = max_requests_per_ip
        self.window_seconds = window_seconds

    async def check_auth_limits(self, *, phone_number: str, ip_address: str | None) -> None:
        """Проверяет лимиты auth-запросов и выбрасывает ошибку при превышении."""
        phone_key = build_auth_phone_key(phone_number)
        phone_attempts = await self.redis_client.incr(phone_key)
        if phone_attempts == 1:
            await self.redis_client.expire(phone_key, self.window_seconds)
        if phone_attempts > self.max_requests_per_phone:
            raise RateLimitExceededError(retry_after_seconds=self.window_seconds)

        if ip_address is not None:
            ip_key = build_auth_ip_key(ip_address)
            ip_attempts = await self.redis_client.incr(ip_key)
            if ip_attempts == 1:
                await self.redis_client.expire(ip_key, self.window_seconds)
            if ip_attempts > self.max_requests_per_ip:
                raise RateLimitExceededError(retry_after_seconds=self.window_seconds)


def build_auth_rate_limiter(
    *,
    redis_client: RedisCounterClient,
    settings: Settings,
) -> RedisAuthRateLimiter:
    """Создает limiter auth-запросов из значений настроек приложения."""
    return RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=settings.auth_rate_limit_max_requests_per_phone,
        max_requests_per_ip=settings.auth_rate_limit_max_requests_per_ip,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

