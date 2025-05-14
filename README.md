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
   ```

### Создайте файл .env:
Создайте файл .env в корне проекта с параметрами, заданными в .env.restore

### Создайте директории:
`mkdir -p config input_files/scripts output_files logs`

### Настройте права для директории логов: 
Убедитесь, что директория ./logs доступна для записи:
- `chmod -R 777 ./logs`
- `sudo chown -R $(whoami):$(whoami) ./logs`

### Запустите приложение:
`docker-compose up --build`

### Для фонового режима: 
`docker-compose up -d`

API будет доступно на http://localhost:5000.

### Проверьте логи:

`cat logs/reports.log`

или

`tail -f logs/reports.log`

а так же 

`docker compose logs -f` 

### Остановка сервиса:
`docker compose down`

## Использование API

### Health-проверка:
`curl http://localhost:5000/health`

### Запуск расчета:
```bash
curl -X POST http://localhost:5000/<CALCULATOR_VERSION>/startCalc \
  -H "Content-Type: application/json" \
  -d '{"calc_id": 111, "report_date": "2023-12-31", "prev_report_date": "2023-11-30", "actual_date": "2023-12-31"}'
```

### Проверка статуса:
`curl http://localhost:5000/getStatus/111`

## Swagger UI
Документация API доступна по адресу:
`http://localhost:5000/docs`

## Устранение неполадок

### Ошибка подключения к БД:
Проверьте параметры в .env и доступность PostgreSQL:

`psql -h your_db_host -U your_db_user -d your_db_name`

### API не отвечает:
Проверьте, что порт 5000 свободен:

`docker ps`

### Логи пустые:
Проверьте права доступа к ./logs и LOGS_PATH в .env.

### Ошибка сборки:
Очистите кэш Docker:

`docker builder prune`,
`docker compose up --build`