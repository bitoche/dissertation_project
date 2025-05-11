# Инструкция по развертыванию

## Требования
- Docker и Docker Compose
- Python 3.11+ (используется внутри Docker-контейнера)
- Доступ к внешней PostgreSQL базе данных (для получения входных данных)
- Стабильное интернет-соединение для установки зависимостей

## Установка

1. **Склонируйте репозиторий**:
   ```bash
   git clone <repository_url>
   cd <repository_name>


Создайте файл .env:Создайте файл .env в корне проекта с параметрами подключения к внешней PostgreSQL базе данных:
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
LOG_LEVEL=INFO
CONFIG_PATH=/app/config.json

Замените your_db_host, your_db_name, your_db_user, your_db_password на реальные значения.

Создайте файл config.json:Создайте файл config.json в корне проекта. Пример:
{
  "paths": {
    "input": "/app/data/input",
    "output": "/app/data/output",
    "scripts": "/app/scripts"
  },
  "db_connection": {
    "host": "${DB_HOST}",
    "port": "${DB_PORT}",
    "database": "${DB_NAME}",
    "user": "${DB_USER}",
    "password": "${DB_PASSWORD}"
  },
  "queries": {
    "input_data": "SELECT * FROM input_data WHERE date = :data_date"
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/calculator.log"
  }
}


Создайте папки для данных, логов и скриптов:
mkdir -p data/input data/output logs scripts


Создайте пример конфигурации расчета:
echo '{"id": "IFRS17"}' > scripts/IFRS17.json


Запустите приложение с помощью Docker Compose:
docker-compose up --build


Флаг --build пересобирает образ при изменениях.
Для фонового режима: docker-compose up -d.

Это запустит Flask-приложение на http://localhost:5000.

Проверка логов:Логи приложения сохраняются в ./logs/calculator.log. Просмотрите их:
cat logs/calculator.log


Остановка сервиса:
docker-compose down



Использование API

Запуск расчета:
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"report_date": "2023-12-31", "prev_report_date": "2023-11-30", "data_date": "2023-12-31", "calc_type": "IFRS17", "calculation_id": "calc_001"}'


Проверка статуса:
curl http://localhost:5000/api/status/calc_001



Устранение неполадок

Ошибка подключения к базе данных: Проверьте параметры DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD в .env и убедитесь, что внешняя PostgreSQL база доступна (psql -h your_db_host -U your_db_user -d your_db_name).
API не отвечает: Убедитесь, что порт 5000 свободен и контейнер работает (docker ps).
Логи не пишутся: Проверьте путь logging.file в config.json и права доступа к папке ./logs.
Выходные файлы не создаются: Убедитесь, что входные данные есть в ./data/input и скрипт расчета в ./scripts/IFRS17.json.
Ошибка сборки из-за psycopg2: Если возникает ошибка pg_config executable not found:
Убедитесь, что Dockerfile включает установку libpq-dev.
Очистите кэш Docker: docker builder prune.
Попробуйте пересобрать: docker-compose up --build.


Ошибка запуска No module named app.__main__: Убедитесь, что Dockerfile и docker-compose.yaml используют CMD ["python", "run.py"] и command: python run.py.