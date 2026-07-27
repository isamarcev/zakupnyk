# why: офіційний образ uv з вшитим Python 3.12 — керування залежностями через uv.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PROCFLOW_HOST=0.0.0.0 \
    PROCFLOW_PORT=8077 \
    PROCFLOW_DATA_DIR=/app/data \
    PROCFLOW_OPEN_BROWSER=false

WORKDIR /app

# why: спершу лише маніфест+лок — шар залежностей кешується окремо від коду.
# --frozen вимагає закомічений uv.lock; --no-dev не тягне dev-групу в прод.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src

EXPOSE 8077

CMD ["python", "-m", "procflow.main.app"]
