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

# Кастомный фильтр для логгера app
class AppLoggerFilter(logging.Filter):
    def filter(self, record):
        if record.levelno < logging.WARNING:
            return False  # Логи ниже WARNING не попадут в файл
        return True

# Кастомный фильтр для консоли логгера app
class AppConsoleFilter(logging.Filter):
    def filter(self, record):
        return True  # Все уровни в консоль

# Настройка логирования
def setup_logging():
    # Форматтеры
    console_formatter = logging.Formatter('%(asctime)s | %(message)s')
    file_formatter = logging.Formatter('[ %(asctime)-10s | %(levelname)-8s | %(name)-10s ] %(message)s')

    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(LOG_LEVEL)

    # Обработчик для файла
    file_handler = None
    try:
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(LOG_LEVEL)
        print(f"Successfully set up file handler for {LOG_FILE}")
    except Exception as e:
        print(f"Failed to set up file handler for {LOG_FILE}: {e}")

    # Настройка логгера app
    app_logger = logging.getLogger('app')
    app_logger.setLevel(LOG_LEVEL)
    app_logger.handlers.clear()
    # Добавляем консольный обработчик с фильтром для всех уровней
    console_handler_app = logging.StreamHandler(sys.stdout)
    console_handler_app.setFormatter(console_formatter)
    console_handler_app.setLevel(LOG_LEVEL)
    console_handler_app.addFilter(AppConsoleFilter('app'))
    app_logger.addHandler(console_handler_app)
    if file_handler:
        # Добавляем файловый обработчик только для WARNING и выше
        file_handler_app = logging.FileHandler(LOG_FILE, mode='a')
        file_handler_app.setFormatter(file_formatter)
        file_handler_app.setLevel(LOG_LEVEL)
        file_handler_app.addFilter(AppLoggerFilter('app'))
        app_logger.addHandler(file_handler_app)
    app_logger.propagate = False

    # Настройка логгера serv
    serv_logger = logging.getLogger('serv')
    serv_logger.setLevel(LOG_LEVEL)
    serv_logger.handlers.clear()
    serv_logger.addHandler(console_handler)
    if file_handler:
        serv_logger.addHandler(file_handler)
    serv_logger.propagate = False

    # Настройка логгеров uvicorn и fastapi
    for logger_name in ('uvicorn', 'fastapi'):
        logger = logging.getLogger(logger_name)
        logger.setLevel('INFO')
        logger.handlers.clear()
        logger.addHandler(console_handler)
        logger.propagate = False

    # Тестовые сообщения
    app_logger.debug("Test DEBUG message for app logger")
    app_logger.info("Test INFO message for app logger")
    app_logger.warning("Test WARNING message for app logger")
    serv_logger.debug("Test DEBUG message for serv logger")
    serv_logger.info("Test INFO message for serv logger")
    serv_logger.warning("Test WARNING message for serv logger")
    print("Logging configuration completed")

setup_logging()