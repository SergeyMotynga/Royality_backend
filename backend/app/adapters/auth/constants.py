"""Константы и ключи Redis для auth-адаптеров."""

REGISTER_EMAIL_KEY_PREFIX = "auth:register:email"
REGISTER_IP_KEY_PREFIX = "auth:register:ip"
EMAIL_VERIFICATION_KEY_PREFIX = "auth:verify"


def build_register_email_key(email: str) -> str:
    """Возвращает Redis-ключ лимита регистрации по email."""
    return f"{REGISTER_EMAIL_KEY_PREFIX}:{email}"


def build_register_ip_key(ip_address: str) -> str:
    """Возвращает Redis-ключ лимита регистрации по IP."""
    return f"{REGISTER_IP_KEY_PREFIX}:{ip_address}"


def build_email_verification_key(email: str) -> str:
    """Возвращает Redis-ключ хранения кода верификации email."""
    return f"{EMAIL_VERIFICATION_KEY_PREFIX}:{email}"
