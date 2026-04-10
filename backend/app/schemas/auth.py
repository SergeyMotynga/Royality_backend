"""Pydantic-схемы для регистрации и авторизации."""

from datetime import datetime

from pydantic import BaseModel


class SignupRequest(BaseModel):
    """Тело запроса регистрации пользователя."""

    login: str
    password: str
    name: str


class SignupResponse(BaseModel):
    """Ответ успешной регистрации."""

    id: str
    login: str
    name: str
    created_at: datetime


class LoginRequest(BaseModel):
    """Тело запроса авторизации пользователя."""

    login: str
    password: str


class LoginResponse(BaseModel):
    """Ответ успешной авторизации пользователя."""

    access_token: str
