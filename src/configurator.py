import json
from src.handlers import replace_all
from pathlib import Path
from config.config import ModuleConfig
import logging
logger = logging.getLogger('app').getChild('rep').getChild('configurator')

def read_configuration_file(proj_param:str):
    configuration_filename = replace_all(
        'reports_config_<proj>.json',
        {'<proj>': proj_param}
    )
    configuration_file_path = Path(ModuleConfig.CONFIGURATION_FILES_PATH, configuration_filename)
    configuration_file_data = {}
    try:
        with open(configuration_file_path, 'r') as f:
            d = json.load(f)
        configuration_file_data = d
    except Exception as e:
        logger.error(f'Cant read configuration file from {configuration_file_path}')
        raise e
    return configuration_file_data

class ReportsConfigurationModel():
    def __init__(self, configuration_file_data:dict):
        self.activated_reports = configuration_file_data['activated_reports']
        self.refs = configuration_file_data['refs']
        self.all_reports = configuration_file_data['all_reports']
        self.configuration_data_dict = configuration_file_data