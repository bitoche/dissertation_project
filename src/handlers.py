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