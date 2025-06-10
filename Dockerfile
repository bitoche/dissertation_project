FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости для psycopg2-binary
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --resume-retries 3 --index-url https://pypi.org/simple/

COPY . .

ENV PYTHONUNBUFFERED=1
ENV LOGS_PATH=/app/logs

EXPOSE 5000

CMD ["python", "-m", "uvicorn", "src.app.gateway:app", "--host", "0.0.0.0", "--port", "5000"]