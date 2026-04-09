# Royality Backend Development Plan

## 1. Цель

Документ фиксирует план backend-разработки проекта **Royality** (социальная сеть для сообщества Clash Royale).

Текущий фокус: запуск устойчивого MVP с базовым социальным контуром:
- авторизация и профиль пользователя;
- лента постов;
- базовая инфраструктура для хранения медиа;
- подготовленная архитектурная база под разделы турниров, колод и кланов.

---

## 2. Архитектурный принцип

Сохраняем слоистую структуру:
- `api/endpoints` — HTTP-слой и контракты;
- `services` — бизнес-логика;
- `validators` — бизнес-ограничения и policy-проверки;
- `crud` — доступ к БД;
- `models` — ORM;
- `schemas` — Pydantic-контракты.

Поток вызовов:
`endpoint -> service -> validators -> crud`.

### 2.1 Разделение `public` и `admin`

- `public` — пользовательские ручки приложения;
- `admin` — ручки админского контура;
- доступ к `admin` через dependency-проверку роли.
- на текущем этапе админский контур в прикладных фичах не реализуется, поддерживаем только архитектурную возможность разделения.

### 2.2 Актуальные договоренности (апрель 2026)

- Docker запускается отдельным compose-проектом `royality`, чтобы избежать конфликтов с другими контейнерами.
- Основной цикл разработки: backend запускается локально, Postgres и MinIO поднимаются в Docker.
- Тесты раскладываются по функциональным файлам (один функционал — один файл).
- Общие моки репозиториев выносятся в отдельный модуль и переиспользуются между тестами.

---

## 3. Рекомендуемая структура проекта

```text
Royality_backend/
  backend/
    app/
      api/
        v1/
          endpoints/
            public/
              health.py
              auth.py
              profile.py
              feed.py
              decks.py
              tournaments.py
              clans.py
            admin/
              health.py
              users.py
              moderation.py
              content.py
          routers.py
        routers.py
      core/
        config.py
        security.py
        exceptions.py
      db/
        base.py
        session.py
      models/
      schemas/
      crud/
      services/
      validators/
      main.py
  docs/
    plans/
    standards/
    templates/
  royality/
    docker-compose.local.yml
```

---

## 4. API v1 (MVP draft)

Базовый префикс: `/api/v1`.

### 4.1 Public

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /profile/me`
- `PATCH /profile/me`
- `GET /feed/posts`
- `POST /feed/posts`
- `GET /feed/posts/{post_id}`
- `POST /feed/posts/{post_id}/likes`
- `DELETE /feed/posts/{post_id}/likes`

### 4.2 Admin

- `GET /admin/health`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}/status`
- `POST /admin/moderation/posts/{post_id}/hide`

---

## 5. План БД (MVP)

### 5.1 Таблицы

- `users`
- `refresh_sessions`
- `user_profiles`
- `posts`
- `post_media`
- `post_likes`
- `comments`

### 5.2 Соглашения

- PK: `UUID`;
- время: только `TIMESTAMPTZ (UTC)`;
- soft delete в пользовательских сущностях;
- индексируем пользовательские и лентовые запросы по `created_at`.

---

## 6. Инфраструктура (старт)

Обязательный контур для текущего этапа:
- `backend`
- `postgres` (`postgres:17`)
- `minio` (+ `minio_init` для инициализации бакетов)

Принцип:
- backend, postgres и minio работают в отдельных контейнерах;
- локально используем `docker-compose` из `royality/`;
- настройки берутся из `.env`.

---

## 7. Sprint Roadmap

### Sprint 0 — Infra bootstrap

- базовый каркас `FastAPI + Poetry`;
- docker-compose для backend/postgres/minio;
- `.env.example` и health-check endpoint;
- базовый CI-скелет.

### Sprint 1 — Auth + Profile

- регистрация/логин/refresh/logout;
- профиль пользователя;
- базовые unit/integration тесты.

### Sprint 2 — Feed MVP

- посты, лайки, комментарии;
- загрузка медиа в MinIO;
- модерационные ограничения.

### Sprint 3 — Decks + Tournaments (MVP)

- публикация колод;
- базовые турниры: создание, просмотр, регистрация.

### Sprint 4 — Clans + Admin

- кланы, приглашения, внутренние чаты (MVP-версия);
- админ-контур для пользователей и контента.

---

## 8. Definition of Done для MVP

MVP backend готов, если:
- реализованы пользовательские сценарии auth/profile/feed;
- медиа-контур MinIO работает;
- миграции стабильны (`alembic upgrade head`);
- unit/integration тесты проходят;
- покрытие не ниже `90%`.

---

## 9. Versioning Policy

- API публикуется версионно (`/api/v1/...`, далее `/api/v2/...`);
- non-breaking изменения идут в текущую версию;
- breaking изменения требуют новой версии.
