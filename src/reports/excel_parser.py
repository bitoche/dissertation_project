import pandas as pd
from src.handlers import get_param
from pathlib import Path
from config.config import AppConfig, ModuleConfig

PROJ_PARAM = AppConfig.PROJ_PARAM
MODULE_INPUT_FILES_PATH = ModuleConfig.MODULE_INPUT_FILES_PATH
CONSTRUCTORS_PATH = Path(MODULE_INPUT_FILES_PATH, 'constructors')

import logging as _logging
logger = _logging.getLogger("serv").getChild("excel_parser")

class ConstructorConfig():
    filepath: Path
    constructor_sheet_name: str
    header: int
    def __init__(self, filepath: Path, constructor_sheet_name: str, header: int):
        self.filepath = filepath
        self.constructor_sheet_name = constructor_sheet_name
        self.header = header

def read_constructor(constructor_config: dict):
    filename = get_param(None, constructor_config, ['filename'])

    logger.info(f'Started read constructor {filename}')

    cconf = ConstructorConfig(filepath=Path(CONSTRUCTORS_PATH, PROJ_PARAM, filename),
                              constructor_sheet_name=get_param('constructor', constructor_config, ['constructor_sheet_name']),
                              header=get_param(2, constructor_config, ['header']))
    try:
        constr_df = pd.read_excel(io=cconf.filepath, 
                                  sheet_name=cconf.constructor_sheet_name, 
                                  header=cconf.header)
    except Exception as e:
        logger.exception(f'Cant read constructor from {cconf.filepath}\n{e}')
        raise Exception(e)
    
    return constr_df
    
    