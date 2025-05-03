from pathlib import Path
from dotenv import load_dotenv
from os import getenv
import logging
log = logging.getLogger('configuration')


def env(var_name:str, default: any = None):
    """
    If param `default` doesnt filled, throws error if not found var in .env
    """
    load_dotenv()
    _v = getenv(var_name)
    if _v == None:
        if default is not None:
            log.warning(f'Param {var_name} not found in .env. Filled to default ({default})')
            return default
        else:
            e = KeyError(f'Param {var_name} not found in .env')
            raise e
    else:
        log.debug(f'Found {var_name} in .env. Recieved variable of type "{type(_v)}"')
        return _v

class DBConfig():
    DB_HOST = env('DB_HOST', 'localhost')
    DB_PORT = env('DB_PORT', '5432')
    DB_USER = env('DB_USER')
    DB_PASS = env('DB_PASS')
    DB_NAME = env('DB_NAME')
    
class AppConfig():
    # parameters of api
    pass

class LoggingConfig():
    LOG_LEVEL = env('LOGGING_LEVEL', 'INFO')
    LOGS_PATH = Path.cwd() / 'src' / 'logs'

class ModuleConfig():
    SCRIPTS_PATH = env('MODULE_SCRIPTS_PATH')
    INPUT_FILES_PATH = env('MODULE_INPUT_FILES_PATH')
    OUTPUT_FILES_PATH = env('MODULE_OUTPUT_FILES_PATH')
