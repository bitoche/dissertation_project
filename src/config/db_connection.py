from config.config import DBConfig
import psycopg2
from ..handlers import replace_all, timer
import logging

logger = logging.getLogger('serv').getChild('db_conn')

def get_connection_row():
    row = replace_all(
        "postgresql://user:pass@host:port/dbname",
        {
            "host": DBConfig.DB_HOST,
            "port": DBConfig.DB_PORT,
            "user": DBConfig.DB_USER,
            "pass": DBConfig.DB_PASS,
            "dbname": DBConfig.DB_NAME
        }
    )
    logger.debug(f'Get connection row: {row}')
    return row

@timer
def check_connection_status():
    logger.debug(f'Get db connection status')
    try:
        conn_str = get_connection_row()
        with psycopg2.connect(conn_str) as conn:
            logger.debug(f'Successfully connected to DB.')
        return "ok"
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return "not connected"
    
def execute_query(query: str, connection):
    with connection as conn:
        try:
            curs = conn.cursor()
            curs.execute(query)
        except Exception as e:
            logger.exception(f'Error while executing query:\n{e}')
            raise e
        finally:
            conn.commit()
    