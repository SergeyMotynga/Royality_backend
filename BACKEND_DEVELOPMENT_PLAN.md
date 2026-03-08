# Royality Backend Development Plan

## 1. Цель

Документ фиксирует изолированный план backend-разработки Royality:
- Product Baseline: `Feed` + `Profile` как первый релизный контур;
- стек: FastAPI, Poetry, Ruff, PostgreSQL, Alembic, Redis, S3-compatible Object Storage, Celery, RabbitMQ, Docker;
- слоистая структура `api/services/crud/validators/models/schemas`;
- обязательное версионирование API;
- отдельная директория для функций валидации.

---

## 2. Архитектурный принцип

Ответственность разделена по слоям:
- `api/endpoints` — HTTP-слой (вход/выход, DI, коды ответов);
- `services` — бизнес-логика сценариев;
- `validators` — переиспользуемые проверки бизнес-ограничений;
- `crud` — доступ к БД;
- `models` — ORM-модели;
- `schemas` — Pydantic-контракты API.

Поток вызовов:
`endpoint -> service -> validators -> crud`.

### 2.1 Явные не-цели на старте
- не внедряем full clean architecture как обязательный стиль на весь проект;
- не внедряем отдельный IoC-контейнер;
- не пишем интерфейсы для каждого класса/репозитория без практической необходимости;
- не усложняем код жестким ООП ради формального соблюдения SOLID.

Принцип: добавляем абстракции только при реальной боли (сложность тестирования, дублирование правил, частая смена интеграций).

---

## 3. Рекомендуемая структура проекта

```text
Royality_backend/
  backend/
    alembic/
      versions/
      env.py
    app/
      api/
        v1/
          endpoints/
            auth.py
            profile.py
            feed.py
          routers.py
        v2/
          endpoints/
          routers.py
        routers.py
      core/
        config.py
        security.py
        logging.py
        exceptions.py
        rate_limit.py
      db/
        base.py
        session.py
      models/
        user.py
        profile.py
        post.py
        post_media.py
        comment.py
        post_like.py
        refresh_session.py
        outbox_event.py
        consumed_event.py
        __init__.py
      schemas/
        auth.py
        profile.py
        feed.py
        media.py
        common.py
        __init__.py
      crud/
        base.py
        auth.py
        profile.py
        feed.py
        media.py
        outbox.py
        __init__.py
      services/
        auth.py
        profile.py
        feed.py
        media_storage.py
        event_publisher.py
        __init__.py
      storage/
        s3_client.py
        presign.py
        __init__.py
      tasks/
        media.py
        notifications.py
        maintenance.py
        __init__.py
      workers/
        celery_app.py
        celery_config.py
        outbox_relay.py
        __init__.py
      validators/
        auth.py
        profile.py
        feed.py
        media.py
        common.py
        __init__.py
      utils/
        pagination.py
        datetime.py
      main.py
    tests/
      unit/
      integration/
      conftest.py
    Dockerfile
    alembic.ini
  infra/
    docker-compose.local.yml
    docker-compose.prod.yml
  .env.example
  Makefile
  pyproject.toml
  ruff.toml
  README.md
```

---

## 4. Роль директории `validators`

`validators` — это бизнес-проверки, которые используются в сервисах:
- права на действие (`может ли пользователь редактировать пост`);
- лимиты и ограничения (`размер поста`, `лимиты операций`);
- консистентность данных перед записью.

Важно:
- `schemas` валидируют формат request/response;
- `validators` валидируют бизнес-правила.

---

## 5. Versioning API

Все ручки публикуются с версией:
- `/api/v1/...`
- `/api/v2/...`

Правила:
- non-breaking изменения: в текущей версии;
- breaking изменения: новая версия;
- старую версию поддерживаем в переходный период.

Базовые группы v1:
- `/api/v1/auth`
- `/api/v1/profile`
- `/api/v1/feed`

Feed-контуры v1:
- `GET /api/v1/feed/home` — лента по подпискам + собственные посты автора;
- `GET /api/v1/feed/global` — глобальная лента публичных постов.

---

## 6. Инфраструктура

### 6.1 Docker сервисы (local)
- `backend`
- `postgres`
- `redis`
- `minio` (локальный S3-compatible storage)
- `rabbitmq` (broker)
- `celery_worker`
- `celery_beat`
- `outbox_relay` (publisher из outbox в Rabbit)

### 6.2 Redis задачи
- refresh-сессии/blacklist;
- rate limit (`auth`, создание постов, комментарии);
- кэш горячих данных (опционально).

### 6.3 Object Storage (S3)
- медиа постов и аватары храним в S3/MinIO;
- в PostgreSQL храним только метаданные и `object_key`;
- upload/download через presigned URL;
- backend не проксирует тяжелые файлы.

### 6.4 RabbitMQ + Celery
- RabbitMQ используется как основной broker для Celery;
- очереди разделяются по назначению: `media`, `notifications`, `maintenance`;
- для надежности внедряются `retry + DLQ + idempotency`;
- критичные бизнес-события публикуются через `outbox`.

### 6.5 Минимальный `.env`
- `APP_TITLE`
- `ENV`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `DATABASE_URL`
- `REDIS_URL`
- `S3_ENDPOINT_URL`
- `S3_REGION`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET_MEDIA`
- `S3_BUCKET_AVATARS`
- `S3_USE_SSL`
- `S3_PRESIGN_EXPIRES_SECONDS`
- `RABBITMQ_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND` (optional)
- `CELERY_DEFAULT_QUEUE`
- `CELERY_RETRY_BACKOFF`
- `CORS_ORIGINS`

---

## 7. План БД (Product Baseline)

Таблицы:
- `users`
- `profiles`
- `follows`
- `posts`
- `post_media`
- `comments`
- `post_likes`
- `refresh_sessions`
- `outbox_events`
- `consumed_events`

Базовые соглашения схемы v1:
- первичные ключи: `UUID`;
- soft delete: поле `deleted_at TIMESTAMPTZ NULL` в бизнес-таблицах;
- дата/время: только `TIMESTAMPTZ` (UTC);
- `posts.visibility`: enum `public | followers | private`.

Ключевые поля `posts`:
- `id` (UUID)
- `author_id` (FK -> `users.id`)
- `text`
- `visibility` (`public | followers | private`)
- `created_at`
- `updated_at`
- `deleted_at`

Ключевые поля `follows`:
- `id` (UUID)
- `follower_id` (FK -> `users.id`)
- `followee_id` (FK -> `users.id`)
- `created_at`
- `deleted_at`
- ограничения: `follower_id != followee_id`, unique active pair для подписки

Правила выдачи ленты:
- `global`: только посты `visibility=public` и `deleted_at IS NULL`;
- `home`: посты авторов, на которых подписан пользователь, плюс собственные посты;
- `home` включает `public` и `followers` посты подписок, а также собственные `private`;
- пагинация: keyset по `(created_at, id)`.

Ключевые поля `post_media`:
- `id`
- `post_id`
- `object_key`
- `mime_type`
- `size_bytes`
- `width`
- `height`
- `duration_seconds`
- `sort_order`
- `created_at`

Ключевые поля `outbox_events`:
- `id`
- `event_id` (unique)
- `event_type`
- `payload`
- `status` (`pending/sent/failed`)
- `created_at`
- `sent_at`

Ключевые поля `consumed_events`:
- `event_id` (unique)
- `consumer_name`
- `processed_at`

Индексы:
- `users(email)` unique
- `posts(visibility, created_at, id)` — global feed
- `posts(author_id, created_at, id)`
- `post_media(post_id, sort_order)`
- `comments(post_id, created_at)`
- `post_likes(post_id, user_id)` unique
- `follows(follower_id, followee_id)` unique
- `follows(follower_id, deleted_at)`
- `follows(followee_id, deleted_at)`
- `outbox_events(status, created_at)`
- `consumed_events(event_id)` unique

Миграции:
- только Alembic;
- одна задача = одна миграция;
- обязательная проверка `alembic upgrade head` в CI.

---

## 8. Медиа-поток (S3)

### 8.1 Upload flow
1. Клиент запрашивает presigned URL у backend.
2. Backend валидирует тип/размер файла и генерирует `object_key`.
3. Клиент загружает файл напрямую в S3/MinIO.
4. Клиент вызывает `confirm` endpoint.
5. Backend записывает метаданные в `post_media` или обновляет аватар профиля.

### 8.2 API draft для медиа
- `POST /api/v1/feed/media/upload-url`
- `POST /api/v1/feed/media/confirm`
- `POST /api/v1/profile/avatar/upload-url`
- `POST /api/v1/profile/avatar/confirm`

### 8.3 Guard-правила
- allowlist MIME типов;
- максимальный размер файла;
- ограничение количества файлов в посте;
- валидация владельца `object_key` при confirm.

---

## 9. Фоновые задачи (Celery + RabbitMQ)

### 9.1 Что уходит в фон
- обработка медиа (preview/metadata/cleanup);
- уведомления (новый пост, комментарии, ответы);
- обслуживающие задачи (cleanup, пересчеты counters);
- публикация и доставка доменных событий.

### 9.2 Надежность доставки
- `Outbox`: событие пишется в БД в одной транзакции с бизнес-операцией;
- `Outbox relay`: отдельный процесс публикует pending-события в RabbitMQ;
- `DLQ`: сообщения после N неудачных попыток уходят в dead-letter очередь;
- `Idempotency`: consumer перед обработкой проверяет `event_id` в `consumed_events`.

### 9.3 Базовые требования к Celery workers
- `acks_late = true` для важных задач;
- retry policy с backoff;
- раздельные очереди и воркеры по нагрузке;
- метрики и логирование ошибок по каждой задаче.

---

## 10. Sprint Roadmap

### Sprint 0 (2-3 дня) — Bootstrap
- инициализация Poetry/FastAPI/Ruff/Alembic;
- подключение PostgreSQL, Redis, MinIO, RabbitMQ;
- каркас папок по структуре документа;
- docker-compose local;
- базовый Makefile;
- `GET /api/health`.

Результат: проект поднимается локально одной командой, включая broker.

### Sprint 1 (4-5 дней) — Auth + Profile + Worker Base
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/avatar/upload-url`
- `POST /api/v1/profile/avatar/confirm`
- первичный запуск `celery_worker` и `celery_beat`.

Результат: рабочая авторизация и профиль с аватаром через S3 + базовая инфраструктура воркеров.

### Sprint 2 (5-6 дней) — Feed + Media Processing
- `POST /api/v1/feed/media/upload-url`
- `POST /api/v1/feed/media/confirm`
- `POST /api/v1/feed/posts`
- `GET /api/v1/feed/home`
- `GET /api/v1/feed/global`
- `GET /api/v1/feed/posts/{post_id}`
- `PATCH /api/v1/feed/posts/{post_id}`
- `DELETE /api/v1/feed/posts/{post_id}`
- `POST /api/v1/feed/posts/{post_id}/comments`
- `GET /api/v1/feed/posts/{post_id}/comments`
- `POST /api/v1/feed/posts/{post_id}/like`
- `DELETE /api/v1/feed/posts/{post_id}/like`
- `POST /api/v1/profile/{user_id}/follow`
- `DELETE /api/v1/profile/{user_id}/follow`
- celery-задачи для post-media обработки.

Результат: социальное ядро baseline + медиаконтент в ленте.

### Sprint 3 (3-4 дня) — Reliability Hardening
- outbox + outbox_relay;
- DLQ + retry policy;
- idempotent consumers;
- интеграционные тесты критичных сценариев;
- cleanup orphan-объектов в S3.

Результат: надежный production-подход доставки событий и фоновых задач.

### Sprint 4+ — Expansion
- `decks` (с медиа и избранным)
- `clans` (приглашения, чат)
- `tournaments`

Каждая новая фича добавляется тем же паттерном:
`api/endpoints + services + validators + crud + schemas + models + tasks`.

---

## 11. Makefile для Windows

Рекомендуемые цели:
- `install`
- `lint`
- `format`
- `test`
- `run`
- `worker`
- `beat`
- `makemigrations`
- `migrate`
- `up`
- `down`
- `logs`

Принцип:
- все команды через `poetry run ...`;
- одинаковые команды на всех машинах команды.

---

## 12. CI minimum

Минимальный pipeline:
1. установка зависимостей;
2. `ruff check .`;
3. `pytest`;
4. `alembic upgrade head` в test-базе;
5. полный integration suite на `Postgres + Redis + MinIO + RabbitMQ`;
6. smoke-тест Celery worker + publish/consume сценария.

---

## 13. Definition of Done для Product Baseline

Product Baseline backend готов, если:
- локальное окружение поднимается одной командой;
- реализованы `auth + profile + feed`;
- медиаконтент работает через S3/MinIO (upload-url + confirm);
- фоновые задачи работают через `Celery + RabbitMQ`;
- реализованы `outbox + DLQ + idempotency` для критичных событий;
- все ручки доступны через `/api/v1/...`;
- миграции стабильны;
- есть unit/integration тесты, integration прогоняется полностью в CI.

---

## 14. Versioning Policy (зафиксировано)

### 14.1 Что именно версионируем
Версионируется API-контракт:
- URL (`/api/v1/...`, `/api/v2/...`)
- request/response схемы
- публичное поведение ручек

По умолчанию не дублируем весь backend для новой версии.

### 14.2 Что переиспользуем между `v1` и `v2`
Остаются общими, пока не нужен breaking change в логике:
- `services`
- `validators`
- `crud`
- `models`

`v1` и `v2` endpoints могут вызывать один и тот же service.

### 14.3 Когда создаем отдельный код для `v2`
Новый код делаем только для затронутой части:
- `api/v2/endpoints/...`
- `schemas/v2/...` (или `api/v2/schemas/...`)
- при необходимости: `services/v2/...` и `validators/v2/...`

Если меняется только контракт, а логика та же, новый сервис не нужен.

### 14.4 Примеры
Non-breaking:
- добавили необязательное поле в ответ;
- добавили query-параметр с default;
- оптимизировали внутреннюю реализацию без изменения контракта.

Breaking:
- переименовали поле ответа;
- изменили тип поля (`int` -> `string`);
- поменяли семантику ручки;
- изменили обязательность полей в request.

### 14.5 Правило поддержки версий
- новая версия публикуется параллельно со старой;
- `v1` получает bugfix'ы в период миграции;
- после согласованного дедлайна `v1` переводится в deprecated и удаляется.

Рекомендуемый SLA миграции клиентов: 60-90 дней после релиза `v2`.

---

## 15. Итог

План покрывает API, БД, инфраструктуру, S3-медиаконтур и надежные фоновые задачи на `Celery + RabbitMQ`.
Это позволяет сразу строить продуктовый backend в production-паттерне без последующего перелома архитектуры.
