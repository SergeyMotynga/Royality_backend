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
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://finguru:finguru@localhost:5432/finguru",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=26, alias="PASSWORD_MAX_LENGTH")
    register_rate_limit_max_requests_per_email: int = Field(
        default=5,
        alias="REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL",
    )
    register_rate_limit_max_requests_per_ip: int = Field(
        default=30,
        alias="REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_IP",
    )
    register_rate_limit_window_seconds: int = Field(
        default=900,
        alias="REGISTER_RATE_LIMIT_WINDOW_SECONDS",
    )
    login_rate_limit_max_requests_per_email: int = Field(
        default=10,
        alias="LOGIN_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL",
    )
    login_rate_limit_max_requests_per_ip: int = Field(
        default=60,
        alias="LOGIN_RATE_LIMIT_MAX_REQUESTS_PER_IP",
    )
    login_rate_limit_window_seconds: int = Field(
        default=900,
        alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS",
    )
    verify_rate_limit_max_requests_per_email: int = Field(
        default=5,
        alias="VERIFY_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL",
    )
    verify_rate_limit_max_requests_per_ip: int = Field(
        default=30,
        alias="VERIFY_RATE_LIMIT_MAX_REQUESTS_PER_IP",
    )
    verify_rate_limit_window_seconds: int = Field(
        default=600,
        alias="VERIFY_RATE_LIMIT_WINDOW_SECONDS",
    )
    email_verification_code_ttl_seconds: int = Field(
        default=600,
        alias="EMAIL_VERIFICATION_CODE_TTL_SECONDS",
    )
    email_verification_max_attempts: int = Field(
        default=5,
        alias="EMAIL_VERIFICATION_MAX_ATTEMPTS",
    )
    email_verification_resend_cooldown_seconds: int = Field(
        default=60,
        alias="EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS",
    )
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@finguru.local", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="FinGuru", alias="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=False, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
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
