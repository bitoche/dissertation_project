# IFRS17 Reports Service

API-сервис для выполнения расчетов IFRS17 отчетов. Подключается к внешней PostgreSQL базе данных и предоставляет эндпоинты для запуска расчетов, получения статуса и проверки состояния.

## Требования
- Docker и Docker Compose
- Доступ к внешней PostgreSQL базе данных
- Стабильное интернет-соединение для установки зависимостей

## Установка

1. **Склонируйте репозиторий**:
   ```bash
   git clone <repository_url>
   cd <repository_name>

### Создайте файл .env:
Создайте файл .env в корне проекта с параметрами:
DB_HOST=your_db_host
DB_PORT=5432
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=your_db_name
PROJ_PARAM=demo1
LOGGING_LEVEL=INFO
LOGS_PATH=/app/logs
MODULE_CONFIGURATION_PATH=/app/config
API_VERSION=v1-auto-assigned
CALCULATOR_VERSION=v1-auto-assigned

### Создайте директории:
mkdir -p config input_files/scripts output_files logs

### Настройте права для директории логов: 
Убедитесь, что директория ./logs доступна для записи:
`chmod -R 777 ./logs`

### Запустите приложение:
docker-compose up --build

### Для фонового режима: 
docker-compose up -d.
API будет доступно на http://localhost:5000.

### Проверьте логи:
cat logs/reports.log
cat logs/reports_api.log
или
tail -f logs/reports.log
tail -f logs/reports_api.log

### Остановка сервиса:
docker-compose down

## Использование API

### Health-проверка:
`curl http://localhost:5000/health`

### Запуск расчета:
`curl -X POST http://localhost:5000/v1-auto-assigned/startCalc \
  -H "Content-Type: application/json" \
  -d '{"calc_id": 111, "report_date": "2023-12-31", "prev_report_date": "2023-11-30", "actual_date": "2023-12-31"}'`

### Проверка статуса:
`curl http://localhost:5000/getStatus/111`

## Swagger UI
Документация API доступна по адресу:
http://localhost:5000/docs

## Устранение неполадок

### Ошибка подключения к БД:
Проверьте параметры в .env и доступность PostgreSQL:psql -h your_db_host -U your_db_user -d your_db_name

### API не отвечает:
Проверьте, что порт 5000 свободен:docker ps

### Логи пустые:
Проверьте права доступа к ./logs и LOGS_PATH в .env.

### Ошибка сборки:
Очистите кэш Docker:docker builder prune
docker-compose up --build