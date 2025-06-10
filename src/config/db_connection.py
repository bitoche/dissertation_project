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
def execute_query(query: str, connection):
    logger.info('Executing query')
    try:
        with psycopg2.connect(connection) as conn:
            logger.debug('connection acquired')
            with conn.cursor() as curs:
                logger.debug('cursor acquired')
                curs.execute(query)
                logger.debug('query executed successfully')
            conn.commit()
            logger.debug('transaction committed')
    except Exception:
        logger.exception('Error while executing query')
        try:
            conn.rollback()
            logger.debug('transaction rolled back')
        except Exception as rollback_exc:
            logger.error(f'rollback failed: {rollback_exc}')
        raise
    