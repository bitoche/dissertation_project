from config.config import DBConfig
import psycopg2
from .handlers import replace_all, suppress

def get_connection_row():
    return replace_all(
        "postgresql://user:pass@host:port/dbname",
    {
        "host": DBConfig.DB_HOST,
        "port": DBConfig.DB_PORT,
        "user": DBConfig.DB_USER,
        "pass": DBConfig.DB_PASS,
        "dbname": DBConfig.DB_NAME
    }) 

def check_connection_status():
    res = suppress(psycopg2.connect, get_connection_row())
    return "ok" if res != "error" else "not connected"