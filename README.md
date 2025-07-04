# IFRS17 Reports Service

API-сервис для выполнения расчетов IFRS17 отчетов. Подключается к внешней PostgreSQL базе данных и предоставляет эндпоинты для запуска расчетов, получения статуса и проверки состояния.

## Структура проекта
```
ReportsModule
├── .env (чувствительные переменные окружения)
├── Dockerfile (инструкция сборки контейнера для Docker)
├── README.md (описание проекта в формате MarkDown)
├── docker-compose.yml (инструкция запуска Docker-контейнеров/а)
├── requirements.txt (зависимости модуля для установки в Docker-контейнер)
├── config
│   ├── config.py (основная конфигурация)
│   ├── log_config.py (установка параметров логирования для модуля)
│   └── reports_config_<название проекта>.json (конфигурация бизнес-логики модуля)
├── input_files (смонтированная директория входных файлов)
│   ├── constructors
│   │   └── <директория с названием проекта>
│   │       └── <excel-файлы конструкторов>
│   └── scripts
│       ├── <основные скрипты>
│       └── subqueries
│           └── <дополнительные скрипты>
├── output_files
│   └── <выходные файлы>
├── logs (директория с файлами логов)
│   └── reports.log
└── src (основной код модуля)
    ├── app (API-слой модуля)
    │   └── gateway.py (основные эндпойнты, запуск самого API)
    ├── config
    │   ├── configurator.py (чтение конфигурации бизнес-логики модуля)
    │   └── db_connection.py (управление подключением к БД)
    ├── handlers.py (утилиты для удобства)
    ├── main.py (калькулятор)
    ├── model (модели pydantic)
    │   └── interface.py
    ├── reports (утилиты для работы с конструктором и скриптами)
    │   ├── excel_parser.py
    │   ├── syntax_parser.py
    │   └── formula_parser.py
    └── tests (тесты модуля)
        └── database_tests.py (тесты подключения и входных таблиц БД)
```

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

# Другие README

> **Описание структуры конфигурационного файла**
> 
> [config/README.md](config/README.md)

> **Описание использования методов загрузки файлов**
> 
> [input_files/README.md](input_files/README.md)

> **Описание использования Excel-конструкторов**
> 
> [input_files/CONSTR_README.md](input_files/CONSTR_README.md)