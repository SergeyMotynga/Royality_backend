# План продолжения: Infra Bootstrap (feature/infra)

## Контекст на текущий момент

- Базовая ветка разработки: `develop` (создана).
- Ветка для инфраструктуры: `feature/infra` (активна).
- Документация и стандарты уже зафиксированы коммитом в `develop`.
- В `feature/infra` пока нет прикладных изменений (кроме неотслеживаемой локальной `.idea/`).

## Цель следующей сессии

Поднять стартовый инженерный каркас проекта в таком порядке:
1. `Poetry` (пакетный менеджер и зависимости).
2. `Makefile` (единые команды разработки).
3. `Ruff` (линт/формат).
4. Базовый backend-каркас.
5. Docker-инфраструктура (`backend + postgres:17 + minio`).

## Пошаговый план

### Шаг 1. Tooling bootstrap (приоритет №1)

Добавить:
- `pyproject.toml` (FastAPI, uvicorn, pydantic-settings, SQLAlchemy, Alembic, psycopg, boto3; dev: pytest, httpx, ruff, pytest-cov).
- `poetry.toml` (локальный режим virtualenv).
- `ruff.toml` (правила линтинга/форматирования).
- `Makefile` (команды: `install`, `lint`, `format`, `test`, `up-local`, `down-local`, `logs-local`).
- `.env.example` (переменные для app/postgres/minio).
- `.dockerignore`.

DoD:
- `poetry check` проходит.
- `make lint` и `make format-check` выполняются (после `poetry install`).

### Шаг 2. Минимальный backend-каркас

Добавить:
- `backend/app/main.py`.
- `backend/app/core/config.py`.
- `backend/app/core/logging.py`.
- `backend/app/core/exceptions.py`.
- `backend/app/api/routers.py`.
- `backend/app/api/v1/routers.py`.
- `backend/app/api/v1/endpoints/public/health.py`.
- `backend/app/api/v1/endpoints/admin/health.py` как архитектурная заготовка admin-контура.
- зависимости доступа (`get_current_user`, `get_current_superuser`) как заготовка для будущих admin-фич.

DoD:
- Поднимается приложение с `uvicorn backend.app.main:app`.
- Доступны `/health`, `/api/v1/health`, `/api/v1/admin/health`.

### Шаг 3. Docker-infra

Добавить:
- `backend/Dockerfile` (Poetry + запуск uvicorn).
- `royality/docker-compose.local.yml`.

Сервисы на старте:
- `postgres` (`postgres:17-alpine`).
- `minio`.
- `minio_init` (инициализация бакетов).

DoD:
- `docker compose --env-file .env -f royality/docker-compose.local.yml up -d postgres minio minio_init` стартует.
- Контейнеры `postgres`, `minio` в состоянии `running`.
- backend может запускаться локально и подключаться к контейнерным `postgres` и `minio`.

### Шаг 4. Smoke-тесты и фиксация

Добавить минимальные интеграционные тесты health endpoint-ов:
- `tests/integration/test_health_endpoints.py`.
- `tests/mocks/repositories.py` для переиспользуемых моков репозиториев.

Проверки:
- `pytest -m integration` (или точечно по файлу).
- `docker compose ... config` без ошибок.

Коммит-пакеты:
1. `chore(tooling): bootstrap poetry make ruff`
2. `feat(backend): add minimal api skeleton`
3. `feat(infra): add docker compose with postgres17 and minio`

## Что делаем первым при возвращении

Начинаем с **Шага 1**: `pyproject.toml`, `poetry.toml`, `ruff.toml`, `Makefile`, `.env.example`, `.dockerignore`.
