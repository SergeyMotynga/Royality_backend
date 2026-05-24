"""Publisher задач отправки SMS-кодов подтверждения."""

from __future__ import annotations

from typing import Protocol


class VerificationSmsTask(Protocol):
    """Контракт задачи отправки SMS-кода подтверждения."""

    def delay(self, phone_number: str, code: str) -> None:
        """Ставит задачу на отправку SMS в очередь воркера."""


class CelerySmsTaskPublisher:
    """Постановщик задач отправки SMS-кодов подтверждения в Celery."""

    def __init__(self, *, send_verification_sms_task: VerificationSmsTask) -> None:
        """Инициализирует publisher с Celery-задачей отправки SMS."""
        self.send_verification_sms_task = send_verification_sms_task

    def enqueue_phone_verification(self, *, phone_number: str, code: str) -> None:
        """Ставит задачу отправки SMS-кода подтверждения в очередь."""
        self.send_verification_sms_task.delay(phone_number, code)

