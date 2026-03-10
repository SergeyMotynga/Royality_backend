"""Publisher задач отправки email-подтверждений."""

from __future__ import annotations

from typing import Protocol


class VerificationEmailTask(Protocol):
    """Контракт Celery-задачи отправки email-подтверждения."""

    def delay(self, email: str, code: str) -> None:
        """Ставит задачу на отправку email в очередь воркера."""


class CeleryEmailTaskPublisher:
    """Постановщик задач отправки email-подтверждения в Celery."""

    def __init__(self, *, send_verification_email_task: VerificationEmailTask) -> None:
        """Инициализирует publisher с Celery-задачей отправки email."""
        self.send_verification_email_task = send_verification_email_task

    def enqueue_email_verification(self, *, email: str, code: str) -> None:
        """Ставит задачу отправки письма подтверждения в очередь."""
        self.send_verification_email_task.delay(email, code)
