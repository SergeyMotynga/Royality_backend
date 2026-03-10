from __future__ import annotations

import pytest
from backend.app.api.v1.endpoints.public.auth import get_client_ip
from starlette.requests import Request

pytestmark = pytest.mark.unit


def _build_request(
    *,
    headers: list[tuple[bytes, bytes]],
    client: tuple[str, int] | None,
) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "scheme": "http",
        "headers": headers,
        "client": client,
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_get_client_ip_uses_forwarded_for_header_first() -> None:
    request = _build_request(
        headers=[(b"x-forwarded-for", b"203.0.113.1, 10.0.0.5")],
        client=("127.0.0.1", 12345),
    )

    assert get_client_ip(request) == "203.0.113.1"


def test_get_client_ip_falls_back_to_direct_client() -> None:
    request = _build_request(headers=[], client=("127.0.0.1", 12345))

    assert get_client_ip(request) == "127.0.0.1"


def test_get_client_ip_returns_none_when_client_missing() -> None:
    request = _build_request(headers=[], client=None)

    assert get_client_ip(request) is None
