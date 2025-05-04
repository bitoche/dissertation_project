import logging
from os.path import join as join_path 
from os import makedirs
from .config import LoggingConfig

LOG_LEVEL = LoggingConfig.LOG_LEVEL
LOGS_PATH = LoggingConfig.LOGS_PATH
LOG_FILE = join_path(LOGS_PATH, 'app.log')
makedirs(LOGS_PATH, exist_ok=True)


def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s | %(levelname)s\t| %(name)s] %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': LOG_FILE,
                'formatter': 'default',
                'mode': 'a',
            },
        },
        'loggers': {
            'app': {
                'handlers': ['file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            # only console out at bottom
            'uvicorn': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'uvicorn.error': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'fastapi': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    })
    logging.info(f'Setted log out to file "{LOG_FILE}" with level "{LOG_LEVEL}"')

setup_logging()