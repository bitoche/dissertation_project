import logging
import logging.config
from os.path import join as join_path
from os import makedirs
from .config import LoggingConfig

LOG_LEVEL = LoggingConfig.LOG_LEVEL
LOGS_PATH = LoggingConfig.LOGS_PATH
LOG_FILE = join_path(LOGS_PATH, 'reports.log')
API_LOG_FILE = join_path(LOGS_PATH, 'reports_api.log')

# Проверяем и создаем директорию для логов
try:
    makedirs(LOGS_PATH, exist_ok=True)
    logging.debug(f"Log directory created or exists: {LOGS_PATH}")
except Exception as e:
    logging.error(f"Failed to create log directory {LOGS_PATH}: {e}")
    # Fallback: выводим логи только в консоль
    LOGS_PATH = None

def setup_logging():
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        }
    }
    
    if LOGS_PATH:
        handlers.update({
            'api_file': {
                'filename': API_LOG_FILE,
                'class': 'logging.FileHandler',
                'formatter': 'time_level_name',
                'mode': 'a',
            },
            'file': {
                'filename': LOG_FILE,
                'class': 'logging.FileHandler',
                'formatter': 'time_level_name',
                'mode': 'a',
            }
        })
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'time_level_name': {
                'format': '[ %(asctime)-10s | %(levelname)-8s | %(name)-10s ] %(message)s',
            },
            'console': {
                'format': '%(asctime)s | %(message)s'
            }
        },
        'handlers': handlers,
        'loggers': {
            'app': {
                'handlers': ['file'] if LOGS_PATH else ['console'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'uvicorn': {
                'handlers': ['console', 'api_file'] if LOGS_PATH else ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'fastapi': {
                'handlers': ['console', 'api_file'] if LOGS_PATH else ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'] if LOGS_PATH else ['console'],
            'level': 'WARNING',
        }
    }
    
    try:
        logging.config.dictConfig(logging_config)
        logging.info(f'Set log output to file "{LOG_FILE}" with level "{LOG_LEVEL}"')
    except Exception as e:
        logging.error(f"Failed to configure logging: {e}")
        # Fallback: минимальная конфигурация только с консолью
        logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s | %(message)s')

setup_logging()