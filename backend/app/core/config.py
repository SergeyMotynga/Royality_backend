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
    )

    app_title: str = Field(default="Royality Backend", alias="APP_TITLE")
    env: str = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
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
