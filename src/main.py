from src.config.db_connection import check_connection_status, get_connection_row
from src.model.interface import GeneralInfo
from src.handlers import timer, get_param
from config.config import AppConfig, ModuleConfig, DBConfig
from src.config.configurator import read_configuration_file, ReportsConfigurationModel, check_logic_of_configuration
import logging
from .reports.excel_parser import read_constructor
from .reports.syntax_parser import prepare_query, sql_variables, sql_variable, SQL_VAR
from pathlib import Path
import pandas as pd
import src.tests.database_tests as module_db_tests

app_log = logging.getLogger('serv')
mf_log = app_log.getChild('main')

MODULE_SCRIPTS_PATH = ModuleConfig.MODULE_SCRIPTS_PATH
DB_SCHEMA_INPUT_DATA = DBConfig.SchemasConfig.DB_SCHEMA_INPUT_DATA
DB_SCHEMA_REPORTS = DBConfig.SchemasConfig.DB_SCHEMA_REPORTS
DB_SCHEMA_REFERENCES = DBConfig.SchemasConfig.DB_SCHEMA_REFERENCES
DB_SCHEMA_SANDBOX = DBConfig.SchemasConfig.DB_SCHEMA_SANDBOX



calc_statuses = {}

class CalcStatus:
    def __init__(self, percent: int, status: str, message: str, calc_id: int):
        self.percent = percent
        self.status = status
        self.message = message
        calc_statuses[calc_id] = self

    def _upd(self, percent: int = None, status: str = None, message: str = None, calc_id: int = None):
        self.percent = percent if percent is not None else self.percent
        self.status = status if status is not None else self.status
        self.message = message if message is not None else self.message
        calc_statuses[calc_id] = self

    def get_dict_status(self):
        return {
            "percent": self.percent,
            "status": self.status,
            "message": self.message
        }

def update_ref(ref_name:str, config: dict):
    from enum import Enum
    class RefConfig(Enum):
        filename = get_param(None, config, ['filename']) 
        header_size = get_param(None, config, ['header'])
        class ColParams(Enum):
            code_col = get_param(None, config, ['cd_col'])
            name_col = get_param(None, config, ['name_col'])
    # если в файле нет cd или name колонки -- отметается
    # for col in enumerate(RefConfig.ColParams):
    #     if col not in df.cols:
    #         raise KeyError(f'Column with name {col} not found in ref {ref_name} cols: {df.cols}')
    # колонки, которые являются необязательными добавляются без проверки
    # 
    

@timer
def start_calc(item: GeneralInfo):
    DB_CONNECTION_ROW = get_connection_row()

    calc_id = item.calc_id
    report_date = item.report_date
    prev_report_date = item.prev_report_date
    actual_date = item.actual_date
    mf_log.info(f'Started task: (calc_id={calc_id}, report_date={report_date}, prev_report_date={prev_report_date}, actual_date={actual_date})')
    
    _status = CalcStatus(
        percent=1,
        status="in_progress",
        message="started",
        calc_id=calc_id
    )

    # тест подключения к бд
    if check_connection_status() == "not connected":
        _status._upd(None, "error", "db connection does not exists", calc_id)
        return _status.get_dict_status()

    reports_config_data = read_configuration_file(AppConfig.PROJ_PARAM)
    
    check_logic_of_configuration(reports_config_data, ignore_errors=False)

    reports_config = ReportsConfigurationModel(reports_config_data)
    activated_reports = reports_config.activated_reports
    refs_configuration = reports_config.refs
    
    mf_log.info(f"Activated reports: {activated_reports}")

    # update refs if needed
    is_needed_refs_update = get_param(True, reports_config.configuration_data_dict, ['general','auto_update_refs'])
    if is_needed_refs_update:
        all_ref_names = [ref_name for ref_name,ref_config in refs_configuration.items()]
        percents_by_load_all_refs = 30
        percents_per_ref = (percents_by_load_all_refs - _status.percent) // len(all_ref_names) 
        for ref_name, ref_config in refs_configuration.items():
            _status._upd(_status.percent + percents_per_ref, "in progress", f"processing load ref {ref_name}", calc_id)
            
            mf_log.info(f'Started update ref {ref_name}')
            update_ref(ref_name, ref_config)
    
    percents_remain = 100 - _status.percent
    percents_per_rep = (percents_remain) // len(activated_reports)
    for rep in activated_reports:

        rlog = mf_log.getChild(rep)
        rlog.info(f"Started report {rep}")

        # чтение конфигурации этого отчета
        rep_config = get_param(None, reports_config.configuration_data_dict, ['reports', rep])
        mart_config = get_param(None, rep_config, ['mart_structure'])

        rep_group_results_source_name = get_param(None, rep_config, 'group_amounts_source')
        group_results_source_config = get_param(None, reports_config.configuration_data_dict, ['sources', 'amounts', rep_group_results_source_name])
        group_results_cols_list = get_param(None, group_results_source_config, ['columns'])
        rep_group_attrs_source_name = get_param(None, rep_config, 'group_attributes_source')
        group_attrs_source_config = get_param(None, reports_config.configuration_data_dict, ['sources', 'attributes', rep_group_attrs_source_name])
        group_attrs_cols_list = get_param(None, group_attrs_source_config, ['columns'])
        
        # тесты
        necessary_tables = [
            (DB_SCHEMA_INPUT_DATA, rep_group_results_source_name, group_results_cols_list), 
            (DB_SCHEMA_INPUT_DATA, rep_group_attrs_source_name, group_attrs_cols_list)
            ]
        for _t in necessary_tables:
            rlog.info(f'Run exist test for {_t[0]}.{_t[1]}')
            test_res = module_db_tests.table_exists_test(_t[0], _t[1], DB_CONNECTION_ROW)
            if test_res != 'ok':
                _ex = f'Relation {_t[0]}.{_t[1]} does not exist in connected database.'
                raise Exception(_ex)
            else:
                # тест столбцов таблицы
                rlog.info(f'Run cols exist test for {_t[0]}.{_t[1]}: {_t[2]}')
                cols_test_res = module_db_tests.cols_exists_test(_t[0], _t[1], _t[2], DB_CONNECTION_ROW)
                if len(cols_test_res) > 0:
                    _t = ''
                    for test_res in cols_test_res:
                        _t += f'{test_res}\n'
                    _ex = _t
                    raise Exception(_ex)

        # чтение конструктора
        rep_using_constructor = get_param(None, mart_config, ['using_constructor'])
        constructor_config = get_param(None, reports_config.configuration_data_dict, ['constructors', rep_using_constructor])
        constructor_df = read_constructor(constructor_config)
        rlog.info(f'constructor:\n{constructor_df}')
        
        # получение уникальных метрик из конструктора
        calc_formula_constructor_col = constructor_df['calc_formula'].astype(str) # столбец с указанием из каких показателей состоит показатель
        unique_used_metrics:list[str] = []
        for metrics_in_row in calc_formula_constructor_col:
            list_row_metrics: list[str] = metrics_in_row.split(",")
            for metric in list_row_metrics:
                metric = metric.strip()
                if metric not in unique_used_metrics:
                    unique_used_metrics.append(metric)
        # / получение уникальных метрик из конструктора

        report_date = sql_variable(rep, SQL_VAR.VARIABLE)(report_date)
        prev_report_date = sql_variable(rep, SQL_VAR.VARIABLE)(prev_report_date)
        actual_date = sql_variable(rep, SQL_VAR.VARIABLE)(actual_date)
        calc_id = sql_variable(rep, SQL_VAR.VARIABLE)(calc_id)

        db_schema_input = sql_variable(rep, SQL_VAR.VARIABLE)(DB_SCHEMA_INPUT_DATA)
        db_schema_rep = sql_variable(rep, SQL_VAR.VARIABLE)(DB_SCHEMA_REPORTS)
        db_schema_ref = sql_variable(rep, SQL_VAR.VARIABLE)(DB_SCHEMA_REFERENCES)
        db_schema_sandbox = sql_variable(rep, SQL_VAR.VARIABLE)(DB_SCHEMA_SANDBOX)

        select_group_attrs_script = open(Path(MODULE_SCRIPTS_PATH, 'subqueries', 'select_group_attrs.sql'), 'r').read()
        select_group_attrs_script = sql_variable(rep, SQL_VAR.STRUCTURE)(select_group_attrs_script)

        select_group_results_script = open(Path(MODULE_SCRIPTS_PATH, 'subqueries', 'select_group_amounts.sql'), 'r').read()
        select_group_results_script = sql_variable(rep, SQL_VAR.STRUCTURE)(select_group_results_script)

        group_results_source_table_name = sql_variable(rep, SQL_VAR.VARIABLE)(rep_group_results_source_name)
        
        # преобразование в str для query
        group_results_cols_list = ", ".join(group_results_cols_list) if len(group_results_cols_list)>0 else 'NOT FOUND COLS'
        group_results_cols_list = sql_variable(rep, SQL_VAR.STRUCTURE)(group_results_cols_list)
        select_group_results_query = prepare_query(select_group_results_script, sql_variables[rep])
        rlog.info(f'Started get group results: \n{select_group_results_query}')
        results_by_groups = pd.read_sql(select_group_results_query, con=DB_CONNECTION_ROW)
        rlog.debug(f'results by groups:\n{results_by_groups}')

        # проверка - заполнены ли все необходимые метрики по группам
        not_filled_metrics: list[str] = []
        for metric in results_by_groups['amount_type_cd']:
            if metric not in unique_used_metrics:
                not_filled_metrics.append(metric)
        if len(not_filled_metrics) > 0:
            _nfmetr_text = ''
            for i, _m in enumerate(not_filled_metrics, 1):
                _nfmetr_text += f'\n{i}. {_m}'
            _ex = f'Report {rep} using not filled in result source metrics:{_nfmetr_text}'
            raise Exception(_ex)
        # / проверка - заполнены ли все необходимые метрики по группам

        group_attrs_cols_list = ", ".join(group_attrs_cols_list) if len(group_attrs_cols_list)>0 else 'NOT FOUND COLS'
        group_attrs_cols_list = sql_variable(rep, SQL_VAR.STRUCTURE)(group_attrs_cols_list)
        
        group_attr_source_table_name = sql_variable(rep, SQL_VAR.VARIABLE)(rep_group_attrs_source_name)


        select_group_attrs_query = prepare_query(select_group_attrs_script, sql_variables[rep])
        rlog.info(f'Started get group attrs: \n{select_group_attrs_query}')
        group_attrs = pd.read_sql(select_group_attrs_query, con=DB_CONNECTION_ROW)
        rlog.debug(f'group attrs:\n{group_attrs}')

        groups_to_calc = ""

        metrics_to_calc_from_constr = constructor_df['metric_name'].drop_duplicates().astype(str) # уникальные названия показателей для расчета
        _com = """
    другой парсер формул:
    split по "and" -> strip -> имеем действия по три. 
    записываем полученные действия в dict (например, and_dict)
    для каждого действия (или если есть значения во временном dict с промежуточными результатами)
        split по " " -> strip -> имеем столбец/значение, оператор, столбец/значение.
        (генерируем условие для пандаса.)
        если первое - значение:
            (значит третье - значение)
            парсим оператор.
            делаем действие со значениями
            если действие (то которые получили после сплита по "and") не одно:
                записываем результат во временный dict (типа {1(номер действия): True или 234 (результат действия)}) 
            если действие - одно:
                записываем результат в переменную (например, result)
        если первое - название столбца (начинается с буквы):
            находим это значение для этой группы (парсер формул применяется для каждой группы, построчно для строк конструктора), этого calc_id и этого столбца. должно быть уникальным. обычно - по атрибутам, так что проблем не должно быть  
            записываем найденное значение в переменную(например val_1)
            если третье - название столбца:
                находим это значение для этой группы, и....
                записываем найденное значение в переменную (например val_2)
            если третье - значение:
                записываем найденное значение в переменную (например val_2)
            парсим оператор
            выполняем действие между значениями.
    //////// не закончено, так как надо сохранить порядок действий, например если сплит не по "and" а по "or" и т д (так же могут быть скобочки)
    //////// пока что столбец filter не будет использоваться
        """
    
        # data_mart_create_script = prepare_query(query=open(Path(MODULE_SCRIPTS_PATH, 'create_rep_data_mart.sql'), 'r').read(),
        #                                         prepared_variables_dict=sql_variables[rep])

        # rlog.info(f'PREPARED QUERY:\n{data_mart_create_script}')

        _status._upd(_status.percent + percents_per_rep, "in progress", f"processing report {rep}", calc_id)

        

    _status._upd(100, "successful", "completed", calc_id)
    # except Exception as e:
    #     mf_log.error(f"Calculation failed: {str(e)}")
    #     _status._upd(None, "error", str(e), calc_id)
    return _status.get_dict_status()

def get_calc_status(calc_id: int):
    try:
        status = calc_statuses[calc_id]
        app_log.info(f'Status of {calc_id} calc is {status.get_dict_status()}')
        return status.get_dict_status()
    except KeyError:
        app_log.warning(f'Calculation {calc_id} not found')
        return {"status": "not_found", "message": "Calculation not found"}