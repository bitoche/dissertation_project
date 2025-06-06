import logging as _l
import time
from functools import wraps

logger = _l.getLogger("serv").getChild('handlers')

def replace_all(text: str, replacements: dict):
    for k, v in replacements.items():
        text = text.replace(str(k), str(v))
    return text

def get_param(default: any, d: dict[str, any], path: list[str] | str, log:bool = True):
    is_path_str = isinstance(path, str)
    if not is_path_str:
        try:
            path_len = len(path)
            curr_data = d
            for path_part_iter in range(path_len):
                try:
                    curr_data = curr_data[path[path_part_iter]]
                except:
                    logger.warning(f'Parameter {path[-1]} turning default ({default}) because: key "{path[path_part_iter]}" not found in dict({[k for k,v in curr_data.items()]})') if log else None
                    return default
                if path_part_iter == path_len - 1:
                    logger.debug(f'Found param {".".join([part for part in path])}: {curr_data}') if log else None
                    return curr_data
        except:
            logger.warning(f'Parameter {path[-1]} doesnt filled, set to default {default}') if log else None
            return default
    else:
        try:
            return d[path]
        except:
            logger.warning(f'Parameter {path} doesnt filled, set to default {default}') if log else None


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        return result
    return wrapper
from pathlib import Path
import os
def create_path_if_not_exists(path:Path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except:
        logger.error(f'Cant create path: {path}')
        return None
    return path

from datetime import datetime
def manual_sleep(seconds: int):
    secs = int(datetime.now().strftime("%S"))+20
    time = datetime.now().strftime(f"%Y_%m_%d_%H_%M_{secs}")
    while datetime.now().strftime(f"%Y_%m_%d_%H_%M_%S") != time:
        continue