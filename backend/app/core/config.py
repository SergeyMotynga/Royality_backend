"""Настройки backend и утилиты для их загрузки."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Рабочие настройки, загружаемые из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_title: str = Field(default="FinGuru Backend", alias="APP_TITLE")
    env: str = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="CHANGE_ME_LOCAL", alias="SECRET_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://user:password@localhost:5432/app",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    auth_rate_limit_max_requests_per_phone: int = Field(
        default=5,
        alias="AUTH_RATE_LIMIT_MAX_REQUESTS_PER_PHONE",
    )
    auth_rate_limit_max_requests_per_ip: int = Field(
        default=30,
        alias="AUTH_RATE_LIMIT_MAX_REQUESTS_PER_IP",
    )
    auth_rate_limit_window_seconds: int = Field(
        default=900,
        alias="AUTH_RATE_LIMIT_WINDOW_SECONDS",
    )

    auth_code_ttl_seconds: int = Field(default=600, alias="AUTH_CODE_TTL_SECONDS")
    auth_code_max_attempts: int = Field(default=5, alias="AUTH_CODE_MAX_ATTEMPTS")
    auth_code_resend_cooldown_seconds: int = Field(
        default=60,
        alias="AUTH_CODE_RESEND_COOLDOWN_SECONDS",
    )

    sms_provider: str = Field(default="noop", alias="SMS_PROVIDER")
    sms_api_base_url: str = Field(default="", alias="SMS_API_BASE_URL")
    sms_api_key: str = Field(default="", alias="SMS_API_KEY")
    sms_sender_id: str = Field(default="", alias="SMS_SENDER_ID")

    api_prefix: str = "/api"
    api_v1_prefix: str = "/v1"

    @property
    def is_production(self) -> bool:
        """Проверяет, запущен ли сервис в production-режиме."""
        return self.env.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек."""
    return Settings()
