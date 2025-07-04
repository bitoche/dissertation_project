import json
from src.handlers import replace_all, get_param
from pathlib import Path
from config.config import ModuleConfig
import logging as _logging
logger = _logging.getLogger('serv').getChild('rep').getChild('configurator')

def read_configuration_file(filename:str):
    configuration_file_path = Path(filename)
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

def check_logic_of_configuration(configuration_in_dict: dict, ignore_errors: bool = False):
    """
    Выводит отчет о логических ошибках в конфигурации JSON модуля . Возвращает 'ok', если ошибок нет, и 'bad' если найдены ошибки.

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
    
    def return_result():
        result = 'ok' if len(errors) == 0 else 'bad'
        text = '\n'.join([f'{i+1}. By check {dict_error["by_check"]} error: {dict_error["message"]}' for i, dict_error in enumerate(errors)]) if result != 'ok' else 'All ok.'
        if not ignore_errors and result == 'bad':
            logger.exception(f'Error message: \n{text}')
            raise Exception(f'Error message: \n{text}')
        else:
            logger.info(f'Full check logic report: {text}')
            return result

    _cfg = configuration_in_dict

    if not isinstance(configuration_in_dict, dict):
        add_error("Configuration must be a dictionary", "GENERAL")
        return return_result()

    refs: dict = get_param({}, _cfg, 'refs')
    if not isinstance(refs, dict):
        add_error("Refs must be a dictionary", "refs")
        return return_result()

    configured_ref_names = [ref_n for ref_n, ref_cfg in refs.items()]

    reports:dict = get_param({}, _cfg, 'reports')
    if not isinstance(reports, dict):
        add_error("Reports must be a dictionary", "rep")
        return return_result()
    if len(reports.keys()) == 0:
        add_error('Not configured reports in configuration', 'rep')
        return_result()

    for rep_name, rep_cfg in _cfg['reports'].items():
        categorical_columns_check_flag = False # станет True, если найдется категориальный столбец
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
        
        # чек прописанности категориальных столбцов и их справочников
        full_categorical_not_groups_cols = [col_desc['name'] for col_desc in _cfg['sources']['categorical_not_groups_cols']]

        logger.debug(f'started init cols check')
        for init_rep_col in rep_cfg['initial_columns']:
            if init_rep_col in full_attr_source_cols:
                continue
            if init_rep_col in full_categorical_not_groups_cols:
                categorical_columns_check_flag = True
                continue
            add_error(f'Report {rep_name} uses init col {init_rep_col}, which not described in attr source {rep_attributes_source} and categorical cols: attrs_cols:{full_attr_source_cols}; categorical_cols:{full_categorical_not_groups_cols}','init cols')

        # constructor сконфигурирован
        constr = rep_cfg["mart_structure"]["using_constructor"]
        configured_constructors = [k for k,v in _cfg['constructors'].items()]
        if constr not in configured_constructors:
            add_error(f'Report {rep_name} uses constructor {constr}, which not configured: {configured_constructors}', 'constr')

        # проверка сконфигурированности категориальных негрупповых столбцов, если такие есть
        if categorical_columns_check_flag:
            for cat_col_not_gr in full_categorical_not_groups_cols:
                try:
                    used_ref = None
                    for cat_col_cfg in _cfg['sources']['categorical_not_groups_cols']:
                        if cat_col_cfg['name'] == cat_col_not_gr:
                            used_ref = cat_col_cfg['using_ref']
                            break
                    if used_ref == None:
                        add_error(f'Report {rep_name} using categorical not gr col {cat_col_not_gr}, which dont described in categorical_not_groups_cols: {full_categorical_not_groups_cols}', 'categorical not gr cols')
                except Exception as e:
                    add_error(f'Exception while check categorical_columns: {e}', 'categorical not gr cols')
                    

        
    # выбрасываем ошибку, если не ignore_errors
    result = 'ok' if len(errors) == 0 else 'bad'
    text = '\n'.join([f'{i+1}. By check {dict_error["by_check"]} error: {dict_error["message"]}' for i, dict_error in enumerate(errors)]) if result != 'ok' else 'All ok.'
    if not ignore_errors and result == 'bad':
        logger.exception(f'Error message: \n{text}')
        raise Exception(f'Error message: \n{text}')
    else:
        logger.info(f'Full check logic report: {text}')
        return result

def find_struct_cols_in_config(rep_name:str, config_dict:dict):
    try:
        errors = []
        returning_dict = {}
        rep_config = get_param(None, config_dict, ['reports', rep_name])
        initial_cols = get_param(None, rep_config, ['initial_columns'])
        results_source = get_param(None, rep_config, ['group_amounts_source'])
        attrs_source = get_param(None, rep_config, ['group_attributes_source'])
        all_columns_from_sources = get_param([], config_dict, ['sources', 'amounts', results_source, 'columns']) + \
            [k for k,v in get_param({}, config_dict, ['sources', 'attributes', attrs_source, 'additional_columns']).items()] + \
            get_param([], config_dict, ['sources', 'attributes', attrs_source, 'columns'])
        logger.info(all_columns_from_sources)
        all_categorical_cols_configs:list[dict] = get_param([], config_dict, ['sources', 'categorical_not_groups_cols'])
        # ремаппинг - создание ключ-значение по названию столбца
        cat_col_conf_dict = {}
        for cat_col_conf in all_categorical_cols_configs:
            cat_col_name = get_param(None, cat_col_conf, ['name'])
            cat_col_ref = get_param(None, cat_col_conf, ['using_ref']) 
            cat_col_conf_dict[cat_col_name] = cat_col_ref
        for col in initial_cols:
            if col not in all_columns_from_sources:
                try:
                    col_conf = {
                        "name": col,
                        "using_ref": cat_col_conf_dict[col]
                    }
                    returning_dict[col] = col_conf
                except:
                    errors.append(f'not found col {col} config')
        if len(errors)>0:
            _ex = '\n'.join(errors)
            raise Exception(_ex)
        return returning_dict

    except Exception:
        raise

class ReportsConfigurationModel():
    def __init__(self, configuration_file_data:dict):
        self.refs = configuration_file_data['refs']
        self.all_reports = configuration_file_data['reports'].keys()
        self.configuration_data_dict = configuration_file_data