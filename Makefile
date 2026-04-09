POETRY ?= poetry
DOCKER_COMPOSE ?= docker compose

COMPOSE_FILE ?= royality/docker-compose.local.yml
ENV_FILE ?= .env
ENV_EXAMPLE_FILE ?= .env.example
MSG ?= auto migration

ifeq ($(OS),Windows_NT)
	ENV_INIT_CMD = powershell -NoProfile -Command "if (!(Test-Path '$(ENV_FILE)')) { Copy-Item '$(ENV_EXAMPLE_FILE)' '$(ENV_FILE)' }"
else
	ENV_INIT_CMD = sh -c '[ -f "$(ENV_FILE)" ] || cp "$(ENV_EXAMPLE_FILE)" "$(ENV_FILE)"'
endif

.PHONY: env-init install lint format format-check test test-coverage run \
	makemigrations migrate migrations-check \
	up-local down-local logs-local up-docker down-docker logs-docker compose-config

env-init:
	$(ENV_INIT_CMD)
	@echo "Заполните $(ENV_FILE) актуальными значениями."

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

test-coverage:
	$(POETRY) run pytest --cov=backend.app --cov-report=term-missing --cov-report=xml --cov-fail-under=90

run:
	$(POETRY) run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

makemigrations:
	$(POETRY) run alembic -c alembic.ini revision --autogenerate -m "$(MSG)"

migrate:
	$(POETRY) run alembic -c alembic.ini upgrade head

migrations-check:
	$(POETRY) run alembic -c alembic.ini upgrade head

up-local: env-init
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d postgres minio minio_init

down-local:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) down --remove-orphans

logs-local:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) logs -f postgres minio

up-docker: env-init
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) --profile backend up -d --build

down-docker:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) --profile backend down --remove-orphans

logs-docker:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) --profile backend logs -f

compose-config:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) --profile backend config
