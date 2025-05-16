import pandas as pd
from src.handlers import get_param
from pathlib import Path
from config.config import AppConfig, ModuleConfig

PROJ_PARAM = AppConfig.PROJ_PARAM
MODULE_INPUT_FILES_PATH = ModuleConfig.MODULE_INPUT_FILES_PATH
CONSTRUCTORS_PATH = MODULE_INPUT_FILES_PATH / 'constructors'

def read_constructor(constructor_config: dict):
    filename = get_param(None, constructor_config, ['filename'])
    filepath = Path(CONSTRUCTORS_PATH, PROJ_PARAM, filename)
    constructor_sheet_name = get_param('constructor', constructor_config, ['constructor_sheet_name'])
    try:
        constr_df = pd.read_excel(filepath, constructor_sheet_name)
    except:
        raise Exception(f'Cant read constructor from {filepath}')