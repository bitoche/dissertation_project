FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости для psycopg2-binary
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --retries 3

COPY . .

# Очищаем временные зависимости
RUN apt-get purge -y --auto-remove gcc

ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.json
ENV LOG_FILE=/app/logs/calculator.log

CMD ["python", "-m", "app"]