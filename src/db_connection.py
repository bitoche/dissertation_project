from config.config import DBConfig
import psycopg2
from .handlers import replace_all, suppress
import logging
logger = logging.getLogger('app')

def get_connection_row():
    row = replace_all(
        "postgresql://user:pass@host:port/dbname",
    {
        "host": DBConfig.DB_HOST,
        "port": DBConfig.DB_PORT,
        "user": DBConfig.DB_USER,
        "pass": DBConfig.DB_PASS,
        "dbname": DBConfig.DB_NAME
    }) 
    logger.debug(f'Get connection row: {row}')
    return 

def check_connection_status():
    res = suppress(psycopg2.connect, get_connection_row())
    logger.debug(f'Get db connection status: {res}')
    return "ok" if res != "error" else "not connected"