FROM python:3.12-slim

WORKDIR /app

# спочатку залежності — щоб кешувався шар між збірками
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PROCFLOW_HOST=0.0.0.0 \
    PROCFLOW_PORT=8077 \
    PROCFLOW_DATA_DIR=/app/data \
    PROCFLOW_OPEN_BROWSER=false

EXPOSE 8077

CMD ["python", "-m", "procflow.main.app"]
