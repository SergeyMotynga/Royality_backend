# FinGuru Backend Development Plan

## 1. Цель

Документ фиксирует план backend-разработки проекта **FinGuru** (AI-ассистент по финансовой грамотности для аудитории 14-22).

Текущий фокус: MVP для пользовательских сценариев внутри банковского приложения:
- AI-чат с безопасными ограничениями;
- финансовые цели;
- симуляторы (кредит/накопления/обучающий инвестиционный сценарий);
- викторины;
- персональные рекомендации;
- контур согласий и аудита.

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

Принцип фиксируем так:
- `public` — ручки пользовательского контура (авторизованный клиент);
- `admin` — ручки админского контура;
- доступ в `admin` только через dependency-проверку роли (`get_current_superuser`).

Важно: `public/admin` — это доменное разделение роутеров и прав, а не про "анонимный" доступ.

---

## 3. Рекомендуемая структура проекта

```text
FinGuru_backend/
  backend/
    app/
      api/
        v1/
          endpoints/
            public/
              auth.py
              profile.py
              consent.py
              assistant_chat.py
              recommendations.py
              goals.py
              simulator.py
              quiz.py
              health.py
            admin/
              users.py
              content.py
              metrics.py
              health.py
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
        refresh_session.py
        user_profile.py
        user_consent.py
        chat_session.py
        chat_message.py
        recommendation.py
        recommendation_action.py
        goal.py
        goal_event.py
        simulator_run.py
        quiz_topic.py
        quiz_question.py
        quiz_attempt.py
        quiz_answer.py
        audit_event.py
        policy_event.py
        outbox_event.py
        consumed_event.py
      schemas/
        auth.py
        profile.py
        consent.py
        assistant_chat.py
        recommendations.py
        goals.py
        simulator.py
        quiz.py
        admin.py
      crud/
        auth.py
        profile.py
        consent.py
        chat.py
        recommendations.py
        goals.py
        simulator.py
        quiz.py
        admin.py
        outbox.py
      services/
        auth.py
        profile.py
        consent.py
        chat_orchestrator.py
        recommendation_engine.py
        goals.py
        simulator.py
        quiz.py
        admin.py
        event_publisher.py
      validators/
        auth.py
        consent.py
        chat_policy.py
        recommendations.py
        goals.py
        simulator.py
        quiz.py
        admin.py
      tasks/
        recalculate_recommendations.py
        send_notifications.py
        cleanup_jobs.py
      workers/
        celery_app.py
        outbox_relay.py
      main.py
```

---

## 4. API v1 (MVP draft)

Базовый префикс: `/api/v1`.

### 4.1 Public (авторизованный пользователь)
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /profile/me`
- `PATCH /profile/me`
- `GET /consent/me`
- `PUT /consent/me`
- `POST /assistant/chat/sessions`
- `POST /assistant/chat/sessions/{session_id}/messages`
- `GET /recommendations/today`
- `POST /recommendations/{id}/actions`
- `POST /goals`
- `GET /goals`
- `PATCH /goals/{goal_id}`
- `POST /goals/{goal_id}/contributions`
- `POST /simulator/credit/calculate`
- `POST /simulator/savings/calculate`
- `POST /simulator/investment/education-scenario`
- `GET /quiz/topics`
- `POST /quiz/attempts`
- `POST /quiz/attempts/{attempt_id}/answers`
- `POST /quiz/attempts/{attempt_id}/complete`

### 4.2 Admin
- `GET /admin/health`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}/status`
- `POST /admin/quiz/topics`
- `POST /admin/quiz/questions`
- `GET /admin/metrics/engagement`
- `GET /admin/policy-events`

---

## 5. План БД (MVP)

### 5.1 Таблицы
- `users`
- `refresh_sessions`
- `user_profiles`
- `user_consents`
- `chat_sessions`
- `chat_messages`
- `recommendations`
- `recommendation_actions`
- `goals`
- `goal_events`
- `simulator_runs`
- `quiz_topics`
- `quiz_questions`
- `quiz_attempts`
- `quiz_answers`
- `audit_events`
- `policy_events`
- `outbox_events`
- `consumed_events`

### 5.2 Соглашения
- PK: `UUID`;
- время: только `TIMESTAMPTZ (UTC)`;
- soft delete в пользовательских сущностях;
- для AI-цепочки фиксируем `trace_id` в `chat_messages` и `policy_events`.

### 5.3 Индексы
- `users(email)` unique;
- `chat_messages(session_id, created_at)`;
- `recommendations(user_id, status, created_at desc)`;
- `goals(user_id, status, created_at desc)`;
- `quiz_attempts(user_id, started_at desc)`;
- `policy_events(trace_id)`;
- `outbox_events(status, created_at)`;
- `consumed_events(event_id)` unique.

---

## 6. AI-policy и регуляторные ограничения

Обязательные правила:
- не выдаем персональные рекомендации по ценным бумагам;
- не обещаем гарантированную доходность;
- по кредитным/инвестиционным запросам всегда добавляем риск-дисклеймер;
- при признаках мошенничества даем безопасный сценарий и эскалацию в поддержку;
- все срабатывания policy пишем в `policy_events`.

---

## 7. Инфраструктура

### 7.1 Обязательный контур (по умолчанию)
- `backend`
- `postgres`
- `redis`

### 7.2 Опциональный async-контур
- `rabbitmq`
- `celery_worker`
- `celery_beat`
- `outbox_relay`

### 7.3 Опциональный OCR/файловый контур
- `minio`
- `minio_init`

Принцип запуска:
- без OCR/async сервисов проект работает на MVP-сценариях;
- OCR включаем только при реальной задаче распознавания чеков;
- async-контур включаем при переносе тяжелых задач в фон.

---

## 8. Конфигурация `.env`

### 8.1 Обязательные переменные
- `APP_TITLE`
- `ENV`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS`

### 8.2 Опциональные
- SMTP и email verification блок;
- S3/MinIO блок (OCR/файлы);
- RabbitMQ/Celery блок (фоновые задачи).

---

## 9. Sprint Roadmap

### Sprint 0 (2-3 дня) — Базовый каркас
- bootstrap FastAPI/Poetry/Ruff;
- миграции и БД;
- `public/admin` роутеры;
- health и базовый CI.

### Sprint 1 (4-5 дней) — Auth/Profile/Consent
- auth flow;
- профиль;
- согласия на персонализацию и коммуникации.

### Sprint 2 (5-6 дней) — Goals/Simulator/Quiz
- цели и прогресс;
- кредитный и накопительный симулятор;
- викторины и учет результатов.

### Sprint 3 (5-6 дней) — Assistant + Recommendations
- AI-чат с policy;
- рекомендации и действия по ним;
- audit/policy events.

### Sprint 4 (3-4 дня) — Admin + Надежность
- админ-ручки контента и метрик;
- outbox/idempotency (если включен async);
- интеграционные тесты критичных сценариев.

---

## 10. Definition of Done для MVP

MVP backend готов, если:
- реализован пользовательский контур `public` и админский контур `admin`;
- AI-чат соблюдает policy-ограничения;
- цели/симуляторы/викторины работают end-to-end;
- рекомендации формируются и логируются;
- миграции стабильны (`alembic upgrade head`);
- unit/integration тесты проходят в CI.

---

## 11. Versioning Policy

- API публикуется версионно (`/api/v1/...`, далее `/api/v2/...`);
- non-breaking изменения идут в текущую версию;
- breaking изменения требуют новой версии;
- старую версию поддерживаем в согласованный переходный период.

---

## 12. Итог

План полностью переключен на домен FinGuru.
Старые контуры соцсети (`feed/posts/comments/likes/follows`) исключены из фокуса и не являются частью MVP.
