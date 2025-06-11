import pandas as pd
from src.handlers import get_param
from pathlib import Path
from config.config import AppConfig, ModuleConfig
from src.model.file_model_intefrace import JSONCrud

MODULE_INPUT_FILES_PATH = ModuleConfig.MODULE_INPUT_FILES_PATH
CONSTRUCTORS_PATH = Path(MODULE_INPUT_FILES_PATH, 'constructors')
REFS_PATH = Path(MODULE_INPUT_FILES_PATH, 'refs')

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
    crud = JSONCrud()
    file_id = get_param(None, constructor_config, ['file_id'])
    filename = crud.get_by_id(file_id).filename

    logger.info(f'Started read constructor {filename}')

    cconf = ConstructorConfig(filepath=Path(filename),
                              constructor_sheet_name=get_param('constructor', constructor_config, ['constructor_sheet_name']),
                              header=get_param(2, constructor_config, ['header']))
    try:
        constr_df = pd.read_excel(io=cconf.filepath, 
                                  sheet_name=cconf.constructor_sheet_name, 
                                  header=cconf.header)
    except Exception as e:
        logger.exception(f'Cant read constructor from {cconf.filepath}\n{e}')
        raise e
    return constr_df

class RefReadModel():
    def __init__(self, filename: str,
    sheet_name: str | int,
    header: int):
        self.filename = filename
        self.sheet_name = sheet_name
        self.header = header
        

def read_ref(ref_read_model: RefReadModel):
    rp = Path(ref_read_model.filename)
    try:
        return pd.read_excel(io=rp, 
                             sheet_name=ref_read_model.sheet_name, 
                             header=ref_read_model.header)
    except Exception as e:
        logger.exception(f'Cant read excel file: {rp}')
        raise e