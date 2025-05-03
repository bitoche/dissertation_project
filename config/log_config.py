import logging
from os.path import join as join_path 
from os import makedirs
from config import log_config

LOG_LEVEL = log_config.LOG_LEVEL
LOGS_PATH = log_config.LOGS_PATH
LOG_FILE = join_path(LOGS_PATH, 'app.log')
makedirs(LOGS_PATH, exist_ok=True)


def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s || %(levelname)s || %(name)s] %(message)s',
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
            'configuration': {
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'calculation': {
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    })
    logging.info(f'Setted log out to file "{LOG_FILE}" with level "{LOG_LEVEL}"')
