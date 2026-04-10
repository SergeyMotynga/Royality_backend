"""Загрузка и хранение настроек приложения."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Набор runtime-настроек backend-приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: InitSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: SecretsSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Определяет порядок источников настроек с приоритетом .env."""
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    app_title: str = Field(alias="ROYALITY_APP_TITLE")
    env: str = Field(alias="ROYALITY_ENV")
    log_level: str = Field(alias="ROYALITY_LOG_LEVEL")
    secret_key: str = Field(alias="ROYALITY_SECRET_KEY")

    app_host: str = Field(alias="ROYALITY_APP_HOST")
    app_port: int = Field(alias="ROYALITY_APP_PORT")

    postgres_user: str = Field(alias="ROYALITY_POSTGRES_USER")
    postgres_password: str = Field(alias="ROYALITY_POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="ROYALITY_POSTGRES_DB")
    postgres_host: str = Field(alias="ROYALITY_POSTGRES_HOST")
    postgres_port: int = Field(alias="ROYALITY_POSTGRES_PORT")
    database_url: str | None = Field(default=None, alias="ROYALITY_DATABASE_URL")

    minio_root_user: str = Field(alias="ROYALITY_MINIO_ROOT_USER")
    minio_root_password: str = Field(alias="ROYALITY_MINIO_ROOT_PASSWORD")
    minio_endpoint: str = Field(alias="ROYALITY_MINIO_ENDPOINT")
    minio_bucket_name: str = Field(alias="ROYALITY_MINIO_BUCKET_NAME")
    minio_region: str = Field(alias="ROYALITY_MINIO_REGION")
    minio_secure: bool = Field(alias="ROYALITY_MINIO_SECURE")

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
