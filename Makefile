# why: uv керує залежностями й venv (.venv); uv run сам синхронізує середовище.
RUN = PYTHONPATH=src uv run python

.PHONY: help setup install run lint fmt typecheck test import-xlsx docker-up docker-down docker-logs clean

help:
	@echo "Доступні команди:"
	@echo "  make setup       — встановити залежності через uv (uv sync)"
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

setup: install
	@echo ""
	@echo "Готово. Спробуйте: make run"

# why: uv sync створює .venv і ставить залежності + dev-групу з pyproject/uv.lock.
install:
	uv sync

run:
	$(RUN) -m procflow.main.app

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

typecheck:
	uv run mypy src

test:
	PYTHONPATH=src uv run pytest

import-xlsx:
	$(RUN) -m procflow.main.import_cli "$(file)"

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
