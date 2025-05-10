FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.json
ENV LOG_FILE=/app/calculator.log

CMD ["python", "-m", "app"]