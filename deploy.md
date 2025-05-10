Инструкция по развертыванию
Требования

Docker
PostgreSQL
Python 3.9+

Установка

Склонируйте репозиторий:

git clone <repository_url>
cd <repository_name>


Создайте файл .env:

DATABASE_URL=postgresql://user:password@host:port/dbname
LOG_LEVEL=INFO
CONFIG_PATH=config.json


Соберите и запустите Docker-контейнер:

docker build -t financial-calculator .
docker run -d -p 5000:5000 --env-file .env financial-calculator


Выполните миграции базы данных:

docker exec <container_name> flask db upgrade

Использование API

Запуск расчета:

curl -X POST http://localhost:5000/api/calculate \
-H "Content-Type: application/json" \
-d '{"report_date": "2023-12-31", "prev_report_date": "2023-11-30", "data_date": "2023-12-31", "calc_type": "IFRS17", "calculation_id": "calc_001"}'


Проверка статуса:

curl http://localhost:5000/api/status/calc_001

