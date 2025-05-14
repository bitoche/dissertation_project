import logging
import sys
from os import makedirs
from os.path import join as join_path
from .config import LoggingConfig

# Основные настройки
LOG_LEVEL = LoggingConfig.LOG_LEVEL
LOGS_PATH = LoggingConfig.LOGS_PATH
LOG_FILE = join_path(LOGS_PATH, 'reports.log')

# Создаем директорию для логов
try:
    makedirs(LOGS_PATH, exist_ok=True)
    print(f"Log directory created or exists: {LOGS_PATH}")
except Exception as e:
    print(f"Failed to create log directory {LOGS_PATH}: {e}")
    # Если не можем создать директорию, продолжаем без файла, логи пойдут в консоль

# Настройка логирования
def setup_logging():
    # Форматтеры
    console_formatter = logging.Formatter('%(asctime)s | %(message)s')
    file_formatter = logging.Formatter('[ %(asctime)-10s | %(levelname)-8s | %(name)-10s ] %(message)s')

    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel('INFO')

    # Обработчик для файла
    file_handler = None
    try:
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel('INFO')
        print(f"Successfully set up file handler for {LOG_FILE}")
    except Exception as e:
        print(f"Failed to set up file handler for {LOG_FILE}: {e}")

    # Настройка логгеров
    # Логгер для app
    app_logger = logging.getLogger('app')
    serv_logger = logging.getLogger('serv')
    loggers = [app_logger,
               serv_logger]
    for l in loggers:
        l.setLevel(LOG_LEVEL)
        l.handlers.clear()
        if file_handler:
            l.addHandler(file_handler)
        else:
            l.addHandler(console_handler)
        l.propagate = False

    # Логгер для uvicorn
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel('INFO')
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.propagate = False

    # Логгер для fastapi
    fastapi_logger = logging.getLogger('fastapi')
    fastapi_logger.setLevel('INFO')
    fastapi_logger.handlers.clear()
    fastapi_logger.addHandler(console_handler)
    fastapi_logger.propagate = False

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel('INFO')
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    # Тестовые сообщения
    app_logger.info("Logging setup completed for app logger")
    uvicorn_logger.info("Logging setup completed for uvicorn logger")
    fastapi_logger.info("Logging setup completed for fastapi logger")
    print("Logging configuration completed")

setup_logging()