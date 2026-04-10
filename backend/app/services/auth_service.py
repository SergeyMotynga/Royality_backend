"""Сервис регистрации и авторизации пользователей."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.crud.user_crud import UserCrud
from backend.app.models.user import User
from backend.app.validators.auth_validators import validate_login, validate_name, validate_password


class AuthValidationError(ValueError):
    """Ошибка валидации входных данных авторизации."""


class LoginAlreadyExistsError(ValueError):
    """Ошибка попытки регистрации с уже занятым логином."""


class InvalidCredentialsError(ValueError):
    """Ошибка неверных учетных данных."""


@dataclass(frozen=True)
class SignupResult:
    """Результат регистрации пользователя."""

    id: UUID
    login: str
    name: str
    created_at: datetime


class AuthService:
    """Бизнес-логика регистрации и авторизации."""

    def __init__(self, user_crud: UserCrud, secret_key: str) -> None:
        self._user_crud = user_crud
        self._secret_key = secret_key

    def signup(self, login: str, password: str, name: str) -> SignupResult:
        """Регистрирует нового пользователя."""
        try:
            validate_login(login)
            validate_password(password)
            validate_name(name)
        except ValueError as exc:
            raise AuthValidationError(str(exc)) from exc

        if self._user_crud.get_by_login(login=login.strip().lower()) is not None:
            raise LoginAlreadyExistsError("Пользователь с таким логином уже существует")

        user = self._user_crud.create_user(
            login=login.strip().lower(),
            password_hash=hash_password(password=password),
            name=name.strip(),
        )
        return SignupResult(
            id=user.id,
            login=user.login,
            name=user.name,
            created_at=user.created_at,
        )

    def login(self, login: str, password: str) -> str:
        """Возвращает access token для корректных учетных данных."""
        user = self._user_crud.get_by_login(login=login.strip().lower())
        if user is None:
            raise InvalidCredentialsError("Неверный логин или пароль")
        if not verify_password(password=password, stored_hash=user.password_hash):
            raise InvalidCredentialsError("Неверный логин или пароль")
        return self._build_access_token(user=user)

    def _build_access_token(self, user: User) -> str:
        """Формирует access token по данным пользователя."""
        return create_access_token(
            secret_key=self._secret_key,
            user_id=str(user.id),
            login=user.login,
            is_superuser=user.is_superuser,
        )
