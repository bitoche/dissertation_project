import pandas as pd
import psycopg2
import logging as _logging

logger = _logging.getLogger("serv").getChild("tester")

def table_exists_test(schema_name:str, table_name:str, conn_str:str):
    with psycopg2.connect(dsn=conn_str) as conn:
        curs = conn.cursor()
        try:
            curs.execute(f'select * from "{schema_name}"."{table_name}"')
            result = 'ok'
            logger.debug(f'Successful! Table "{schema_name}"."{table_name}" exists.')
        except:
            logger.debug(f'Error! Table "{schema_name}"."{table_name}" does not exists.')
            result = 'bad'
        finally:
            conn.rollback()
    return result

def cols_exists_test(schema_name:str, table_name:str, cols:list[str], conn_str:str):
    with psycopg2.connect(dsn=conn_str) as conn:
        curs = conn.cursor()
        errors = []
        for col in cols:
            try:
                curs.execute(f'select "{col}" from "{schema_name}"."{table_name}"')
                logger.debug(f'Successful! Col "{col}" of "{schema_name}"."{table_name}" exists.')
            except:
                logger.debug(f'Error! Column "{col}" of "{schema_name}"."{table_name}" does not exists.')
                errors.append(f'Column "{col}" of "{schema_name}"."{table_name}" does not exists.')
            finally:
                conn.rollback()
    return errors