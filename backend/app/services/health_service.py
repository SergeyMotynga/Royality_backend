"""Сервис health-проверок."""


def build_health_payload(scope: str, user_id: str | None = None) -> dict[str, str]:
    """Формирует унифицированный payload health-ответа."""
    payload = {"status": "ok", "scope": scope}
    if user_id is not None:
        payload["user_id"] = user_id
    return payload
