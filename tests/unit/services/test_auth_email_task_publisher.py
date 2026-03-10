from __future__ import annotations

import pytest
from backend.app.adapters.auth.email_task_publisher import CeleryEmailTaskPublisher

pytestmark = pytest.mark.unit


class _FakeTask:
    def __init__(self) -> None:
        self.delay_calls: list[tuple[str, str]] = []

    def delay(self, email: str, code: str) -> None:
        self.delay_calls.append((email, code))


def test_email_task_publisher_sends_to_delay() -> None:
    task = _FakeTask()
    publisher = CeleryEmailTaskPublisher(send_verification_email_task=task)

    publisher.enqueue_email_verification(email="user@example.com", code="123456")

    assert task.delay_calls == [("user@example.com", "123456")]
