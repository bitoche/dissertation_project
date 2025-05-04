import logging
logger = logging.getLogger("app")

def replace_all(text:str, replacements:dict):
    for k,v in replacements.items():
        text = text.replace(str(k), str(v))
    return text

def suppress(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.error(e)
        return "error"
    
def get_param(default:any, d:dict, path:list[str]):
    try:
        path_len = len(path)
        curr_data = d
        for path_part_iter in range(path_len):
            try:
                curr_data = curr_data[path[path_part_iter]]
            except:
                logger.warning(f'Parameter {path[-1]} turning default ({default}) because: key {path[path_part_iter]} not found in dict({curr_data})')
                return default
            if path_part_iter == path_len-1:
                logger.debug(f'Found param {path[-1]}: {curr_data}')
                return curr_data
    except:
        logger.warning(f'Parameter {path[-1]} doesnt filled, set to default {default}')
        return default

import time
from functools import wraps
def timer(func):
    @wraps(func)  
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Засекаем время начала
        result = func(*args, **kwargs)  # Вызываем исходную функцию
        end_time = time.time()  # Засекаем время окончания
        execution_time = end_time - start_time  # Разница
        logger.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        return result  # Возвращаем результат выполнения функции
    return wrapper
