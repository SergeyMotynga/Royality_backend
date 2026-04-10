"""Валидаторы для сценариев авторизации и регистрации."""


def validate_login(login: str) -> None:
    """Проверяет корректность логина."""
    normalized = login.strip()
    if len(normalized) < 3:
        raise ValueError("Логин должен содержать минимум 3 символа")
    if " " in normalized:
        raise ValueError("Логин не должен содержать пробелы")


def validate_password(password: str) -> None:
    """Проверяет корректность пароля."""
    if len(password) < 8:
        raise ValueError("Пароль должен содержать минимум 8 символов")


def validate_name(name: str) -> None:
    """Проверяет корректность отображаемого имени."""
    if len(name.strip()) < 2:
        raise ValueError("Имя должно содержать минимум 2 символа")
