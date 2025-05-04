import logging
from os.path import join as join_path 
from os import makedirs
from .config import LoggingConfig

LOG_LEVEL = LoggingConfig.LOG_LEVEL
LOGS_PATH = LoggingConfig.LOGS_PATH
LOG_FILE = join_path(LOGS_PATH, 'reports.log')
API_LOG_FILE = join_path(LOGS_PATH, 'reports_api.log')
makedirs(LOGS_PATH, exist_ok=True)


def setup_logging():
    logging.config.dictConfig({
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
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'api_file': {
                'filename': API_LOG_FILE,
                'class': 'logging.FileHandler',
                'formatter': 'time_level_name'
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': LOG_FILE,
                'formatter': 'time_level_name',
                'mode': 'a',
            }
        },
        'loggers': {
            'app': {
                'handlers': ['file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            # only console out at bottom
            'uvicorn': {
                'handlers': ['console', 'api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'uvicorn.error': {
                'handlers': ['console', 'api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'uvicorn.access': {
                'handlers': ['console', 'api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'fastapi': {
                'handlers': ['console', 'api_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        }
    })
    logging.info(f'Setted log out to file "{LOG_FILE}" with level "{LOG_LEVEL}"')

setup_logging()