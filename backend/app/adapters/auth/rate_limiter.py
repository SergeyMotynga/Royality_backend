"""Redis-адаптер проверки лимитов регистрации."""

from __future__ import annotations

from typing import Protocol

from backend.app.adapters.auth.constants import build_register_email_key, build_register_ip_key
from backend.app.core.config import Settings
from backend.app.core.exceptions import RateLimitExceededError


class RedisCounterClient(Protocol):
    """Минимальный контракт Redis-клиента для счетчиков rate-limit."""

    async def incr(self, key: str) -> int:
        """Увеличивает счетчик ключа и возвращает новое значение."""

    async def expire(self, key: str, ttl_seconds: int) -> None:
        """Устанавливает TTL для ключа счетчика."""


class RedisRegisterRateLimiter:
    """Rate-limit регистрации по email и IP через Redis-счетчики."""

    def __init__(
        self,
        *,
        redis_client: RedisCounterClient,
        max_requests_per_email: int,
        max_requests_per_ip: int,
        window_seconds: int,
    ) -> None:
        """Инициализирует параметры лимитов и Redis-клиент."""
        self.redis_client = redis_client
        self.max_requests_per_email = max_requests_per_email
        self.max_requests_per_ip = max_requests_per_ip
        self.window_seconds = window_seconds

    async def check_register_limits(self, *, email: str, ip_address: str | None) -> None:
        """Проверяет лимиты регистрации и выбрасывает ошибку при превышении."""
        email_key = build_register_email_key(email)
        email_attempts = await self.redis_client.incr(email_key)
        if email_attempts == 1:
            await self.redis_client.expire(email_key, self.window_seconds)
        if email_attempts > self.max_requests_per_email:
            raise RateLimitExceededError(retry_after_seconds=self.window_seconds)

        if ip_address is not None:
            ip_key = build_register_ip_key(ip_address)
            ip_attempts = await self.redis_client.incr(ip_key)
            if ip_attempts == 1:
                await self.redis_client.expire(ip_key, self.window_seconds)
            if ip_attempts > self.max_requests_per_ip:
                raise RateLimitExceededError(retry_after_seconds=self.window_seconds)


def build_register_rate_limiter(
    *,
    redis_client: RedisCounterClient,
    settings: Settings,
) -> RedisRegisterRateLimiter:
    """Создает limiter регистрации из значений настроек приложения."""
    return RedisRegisterRateLimiter(
        redis_client=redis_client,
        max_requests_per_email=settings.register_rate_limit_max_requests_per_email,
        max_requests_per_ip=settings.register_rate_limit_max_requests_per_ip,
        window_seconds=settings.register_rate_limit_window_seconds,
    )
