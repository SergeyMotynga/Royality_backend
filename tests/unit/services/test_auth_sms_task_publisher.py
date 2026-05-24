from __future__ import annotations

import pytest
from backend.app.adapters.auth.sms_task_publisher import CelerySmsTaskPublisher

pytestmark = pytest.mark.unit


class _FakeTask:
    def __init__(self) -> None:
        self.delay_calls: list[tuple[str, str]] = []

    def delay(self, phone_number: str, code: str) -> None:
        self.delay_calls.append((phone_number, code))


def test_sms_task_publisher_sends_to_delay() -> None:
    task = _FakeTask()
    publisher = CelerySmsTaskPublisher(send_verification_sms_task=task)

    publisher.enqueue_phone_verification(phone_number="+79991234567", code="123456")

    assert task.delay_calls == [("+79991234567", "123456")]
