"""Настройка логирования приложения."""

from __future__ import annotations

import logging
from logging.config import dictConfig


def setup_logging(log_level: str = "INFO") -> None:
    """Настраивает единый формат логов для backend-сервиса."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level.upper(),
                    "formatter": "default",
                },
            },
            "root": {
                "level": log_level.upper(),
                "handlers": ["console"],
            },
        }
    )

    logging.getLogger(__name__).debug("Логирование настроено, уровень=%s", log_level.upper())
