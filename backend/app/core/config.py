"""Загрузка и хранение настроек приложения."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Набор runtime-настроек backend-приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_title: str = Field(alias="APP_TITLE")
    env: str = Field(alias="ENV")
    log_level: str = Field(alias="LOG_LEVEL")

    app_host: str = Field(alias="APP_HOST")
    app_port: int = Field(alias="APP_PORT")

    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    minio_root_user: str = Field(alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(alias="MINIO_ROOT_PASSWORD")
    minio_endpoint: str = Field(alias="MINIO_ENDPOINT")
    minio_bucket_name: str = Field(alias="MINIO_BUCKET_NAME")
    minio_region: str = Field(alias="MINIO_REGION")
    minio_secure: bool = Field(alias="MINIO_SECURE")

    @property
    def resolved_database_url(self) -> str:
        """Возвращает DSN БД из явного URL или собранный из частей."""
        if self.database_url:
            return self.database_url
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек."""
    return Settings()
