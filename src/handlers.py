import logging
clog = logging.getLogger("calculator")

def replace_all(text:str, replacements:dict):
    for k,v in replacements.items():
        text = text.replace(str(k), str(v))
    return text

def suppress(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        clog.error(e)
        return "error"
    
def get_param(default:any, d:dict, path:list[str]):
    try:
        path_len = len(path)
        curr_data = d
        for path_part_iter in range(path_len):
            try:
                curr_data = curr_data[path[path_part_iter]]
            except:
                clog.warning(f'Parameter {path[-1]} turning default ({default}) because: key {path[path_part_iter]} not found in dict({curr_data})')
                return default
            if path_part_iter == path_len-1:
                clog.debug(f'Found param {path[-1]}: {curr_data}')
                return curr_data
    except:
        clog.warning(f'Parameter {path[-1]} doesnt filled, set to default {default}')
        return default