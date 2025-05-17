import json
from src.handlers import replace_all
from pathlib import Path
from config.config import ModuleConfig
import logging as _logging
logger = _logging.getLogger('serv').getChild('rep').getChild('configurator')

def read_configuration_file(proj_param:str):
    configuration_filename = replace_all(
        'reports_config_<proj>.json',
        {'<proj>': proj_param}
    )
    configuration_file_path = Path(ModuleConfig.CONFIGURATION_FILES_PATH, configuration_filename)
    logger.info(f'Started read configuration file {configuration_file_path}')
    configuration_file_data = {}
    try:
        with open(configuration_file_path, 'r') as f:
            d = json.load(f)
        configuration_file_data = d
    except Exception as e:
        logger.error(f'Cant read configuration file from {configuration_file_path}')
        raise e
    return configuration_file_data

def check_logic_of_configuration(configuration_in_dict: dict = read_configuration_file('demo1'), ignore_errors: bool = False):
    """
    Выводит отчет о логических ошибках в конфигурации JSON модуля (`reports_config_<proj_param>.json`). Возвращает 'ok', если ошибок нет, и 'bad' если найдены ошибки.

    :param configuration_in_dict: Прочитанный dict JSON-конфигурации модуля. Если его не задать, будет читаться конфигурация с постфиксом `demo1`.
    :param ignore_errors: Параметр, при `True` которого метод не выбросит ошибки при нахождении логических ошибок в конфигурации. По умолчанию `False`

    Реализованные проверки:
    ---
    - Проверка подключенных в отчет справочников на сконфигурированность;
    - Проверка подключенных в отчет источников на сконфигурированность;
    - Проверка initial cols отчета на описание в источнике;
    - Проверка конструктора на сконфигурированность.
    """
    errors: list[dict] = []
    def add_error(message:str, by_check: str):
        er_mes = message,
        logger.error(er_mes)
        errors.append({'message': message, 'by_check': by_check})

    _cfg = configuration_in_dict

    configured_ref_names = [ref_n for ref_n, ref_cfg in _cfg['refs'].items()]
    
    for rep_name, rep_cfg in _cfg['reports'].items():
        logger.info(f'Started check logic of report "{rep_name}" configuration')
        # используемые в отчетах справочники должны быть описаны в конфигурации справочников
        logger.debug(f'started used refs config check')
        for using_ref in rep_cfg['mart_structure']['using_refs']:
            if (using_ref not in configured_ref_names):
                add_error(f'Report {rep_name} uses ref {using_ref}, which dont implemented in configuration: {configured_ref_names}', 'ref')
        
        rep_attributes_source = rep_cfg['group_attributes_source']
        rep_amounts_source = rep_cfg['group_amounts_source']

        configured_attributes_sources = [k for k,v in _cfg['sources']['attributes'].items()]
        configured_amounts_sources = [k for k,v in _cfg['sources']['amounts'].items()]
        logger.debug(f'started used sources config check')
        # необходимые source сконфигурированы
        if rep_attributes_source not in configured_attributes_sources:
            add_error(f'Report {rep_name} uses attr source {rep_attributes_source}, which not implemented in configuration: {configured_attributes_sources}', 'attr source')
        if rep_amounts_source not in configured_amounts_sources:
            add_error(f'Report {rep_name} uses attr source {rep_amounts_source}, which not implemented in configuration: {configured_amounts_sources}', 'amount source')
        
        # в source должны быть столбцы, которые указаны как initial отчета
        full_attr_source_cols = \
            _cfg['sources']['attributes'][rep_attributes_source]['columns'] \
            + [k for k,v in _cfg['sources']['attributes'][rep_attributes_source]['additional_columns'].items()]
        logger.debug(f'started init cols check')
        for init_rep_col in rep_cfg['initial_columns']:
            if init_rep_col not in full_attr_source_cols:
                add_error(f'Report {rep_name} uses init col {init_rep_col}, which not described in attr source {rep_attributes_source} cols: {full_attr_source_cols}','init cols')

        # constructor сконфигурирован
        constr = rep_cfg["mart_structure"]["using_constructor"]
        configured_constructors = [k for k,v in _cfg['constructors'].items()]
        if constr not in configured_constructors:
            add_error(f'Report {rep_name} uses constructor {constr}, which not configured: {configured_constructors}', 'constr')
        
    # выбрасываем ошибку, если не ignore_errors
    result = 'ok' if len(errors) == 0 else 'bad'
    text = '\n'.join([f'{i+1}. By check {dict_error["by_check"]} error: {dict_error["message"]}' for i, dict_error in enumerate(errors)]) if result != 'ok' else 'All ok.'
    if not ignore_errors and result == 'bad':
        logger.exception(f'Error message: \n{text}')
        raise Exception(f'Error message: \n{text}')
    else:
        logger.info(f'Full check logic report: \n{text}')
        return result


class ReportsConfigurationModel():
    def __init__(self, configuration_file_data:dict):
        self.activated_reports = configuration_file_data['activated_reports']
        self.refs = configuration_file_data['refs']
        self.all_reports = configuration_file_data['all_reports']
        self.configuration_data_dict = configuration_file_data