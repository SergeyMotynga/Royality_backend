"""Константы и ключи Redis для auth-адаптеров."""

AUTH_PHONE_KEY_PREFIX = "auth:phone"
AUTH_IP_KEY_PREFIX = "auth:ip"
AUTH_CODE_KEY_PREFIX = "auth:code"


def build_auth_phone_key(phone_number: str) -> str:
    """Возвращает Redis-ключ лимита по номеру телефона."""
    return f"{AUTH_PHONE_KEY_PREFIX}:{phone_number}"


def build_auth_ip_key(ip_address: str) -> str:
    """Возвращает Redis-ключ лимита по IP."""
    return f"{AUTH_IP_KEY_PREFIX}:{ip_address}"


def build_auth_code_key(phone_number: str) -> str:
    """Возвращает Redis-ключ хранения OTP-кода по номеру телефона."""
    return f"{AUTH_CODE_KEY_PREFIX}:{phone_number}"

