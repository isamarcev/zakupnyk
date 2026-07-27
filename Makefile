PYTHON ?= python3
VENV   ?= .venv

.PHONY: help setup venv install run lint fmt typecheck test import-xlsx docker-up docker-down docker-logs clean

help:
	@echo "Доступні команди:"
	@echo "  make setup       — повна первинна налаштування (venv + deps)"
	@echo "  make run         — запустити веб-додаток (http://127.0.0.1:8077)"
	@echo "  make lint        — ruff check"
	@echo "  make fmt         — ruff format"
	@echo "  make typecheck   — mypy"
	@echo "  make test        — pytest"
	@echo "  make import-xlsx file=шлях.xlsx — імпорт потреби з Excel"
	@echo "  make docker-up   — зібрати і запустити в Docker (порт 8077)"
	@echo "  make docker-down — зупинити Docker-контейнер"
	@echo "  make docker-logs — логи контейнера"
	@echo "  make clean       — почистити кеші"

setup: venv install
	@echo ""
	@echo "Готово. Спробуйте: make run"

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements-dev.txt

run:
	PYTHONPATH=src $(VENV)/bin/python -m procflow.main.app

lint:
	$(VENV)/bin/ruff check src tests

fmt:
	$(VENV)/bin/ruff format src tests

typecheck:
	$(VENV)/bin/mypy src

test:
	PYTHONPATH=src $(VENV)/bin/pytest

import-xlsx:
	PYTHONPATH=src $(VENV)/bin/python -m procflow.main.import_cli "$(file)"

docker-up:
	docker compose up --build -d
	@echo "Працює: http://localhost:$${PROCFLOW_PUBLIC_PORT:-8077}"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
