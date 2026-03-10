POETRY ?= poetry
DOCKER_COMPOSE ?= docker compose

COMPOSE_LOCAL_FILE ?= infra/docker-compose.local.yml
COMPOSE_PROD_FILE ?= infra/docker-compose.prod.yml
COMPOSE_FILE ?= $(COMPOSE_LOCAL_FILE)
MSG ?= auto migration
MIGRATIONS_DATABASE_URL ?= postgresql+psycopg://royality:royality@localhost:5432/royality

ENV_FILE ?= .env
ENV_EXAMPLE_FILE ?= .env.example

ifeq ($(OS),Windows_NT)
	DETECTED_OS := windows
	PYTHON ?= py -3.12
	ENV_INIT_CMD = powershell -NoProfile -Command "if (!(Test-Path '$(ENV_FILE)')) { Copy-Item '$(ENV_EXAMPLE_FILE)' '$(ENV_FILE)' }"
	ALEMBIC_DB_ENV_PREFIX = set "DATABASE_URL=$(MIGRATIONS_DATABASE_URL)" &&
else
	DETECTED_OS := linux
	PYTHON ?= python3
	ENV_INIT_CMD = sh -c '[ -f "$(ENV_FILE)" ] || cp "$(ENV_EXAMPLE_FILE)" "$(ENV_FILE)"'
	ALEMBIC_DB_ENV_PREFIX = DATABASE_URL=$(MIGRATIONS_DATABASE_URL)
endif

.PHONY: info env-init install lint format format-check test test-unit test-integration test-coverage todo-stubs \
	pre-commit-install pre-commit-run pre-commit-run-push \
	run worker beat outbox makemigrations migrate migrations-check \
	up down logs up-local down-local logs-local up-prod down-prod logs-prod

info:
	@echo "OS=$(DETECTED_OS)"
	@echo "POETRY=$(POETRY)"
	@echo "DOCKER_COMPOSE=$(DOCKER_COMPOSE)"
	@echo "ENV_FILE=$(ENV_FILE)"

env-init:
	$(ENV_INIT_CMD)
	@echo "Populate $(ENV_FILE) with actual values before running services."

install:
	$(POETRY) install --with dev

lint:
	$(POETRY) run ruff check .

format:
	$(POETRY) run ruff format .

format-check:
	$(POETRY) run ruff format --check .

test:
	$(POETRY) run pytest

test-unit:
	$(POETRY) run pytest -m unit

test-integration:
	$(POETRY) run pytest -m integration

test-coverage:
	$(POETRY) run pytest --cov=backend.app --cov-report=term-missing --cov-report=xml

todo-stubs:
	@$(POETRY) run python -c "from pathlib import Path; marker='TODO-INFRA-STUB'; root=Path('.'); found=False; \
for path in root.rglob('*'): \
    if path.is_file() and '.git' not in path.parts and '.venv' not in path.parts: \
        text=path.read_text(encoding='utf-8', errors='ignore'); \
        if marker in text: \
            found=True; \
            print(path); \
if not found: print('No TODO-INFRA-STUB markers found.')"

pre-commit-install:
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit install --hook-type pre-push

pre-commit-run:
	$(POETRY) run pre-commit run --all-files

pre-commit-run-push:
	$(POETRY) run pre-commit run --all-files --hook-stage pre-push

run:
	$(POETRY) run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	@echo "[TODO] replace with celery worker command after worker bootstrap is created"

beat:
	@echo "[TODO] replace with celery beat command after scheduler bootstrap is created"

outbox:
	@echo "[TODO] replace with outbox relay command after relay bootstrap is created"

makemigrations:
	$(ALEMBIC_DB_ENV_PREFIX) $(POETRY) run alembic -c alembic.ini revision --autogenerate -m "$(MSG)"

migrate:
	$(ALEMBIC_DB_ENV_PREFIX) $(POETRY) run alembic -c alembic.ini upgrade head

migrations-check:
	$(ALEMBIC_DB_ENV_PREFIX) $(POETRY) run alembic -c alembic.ini upgrade head

up:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down --remove-orphans

logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

up-local: env-init
	$(DOCKER_COMPOSE) -f $(COMPOSE_LOCAL_FILE) up -d

down-local:
	$(DOCKER_COMPOSE) -f $(COMPOSE_LOCAL_FILE) down --remove-orphans

logs-local:
	$(DOCKER_COMPOSE) -f $(COMPOSE_LOCAL_FILE) logs -f

up-prod: env-init
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD_FILE) up -d

down-prod:
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD_FILE) down --remove-orphans

logs-prod:
	$(DOCKER_COMPOSE) -f $(COMPOSE_PROD_FILE) logs -f
