from src.config.db_connection import get_connection_row, execute_query
from src.model.interface import GeneralInfo, calc_date_fmts
from src.handlers import timer, get_param, create_path_if_not_exists, manual_sleep
from config.config import AppConfig, ModuleConfig, DBConfig
from src.config.configurator import read_configuration_file, ReportsConfigurationModel, check_logic_of_configuration
import logging as _logging
from .reports.excel_parser import read_constructor, read_ref, RefReadModel
from .reports.syntax_parser import prepare_query, sql_variables, sql_variable, SQL_VAR
from pathlib import Path
import pandas as pd
import src.tests.database_tests as module_db_tests
from datetime import datetime

app_log = _logging.getLogger('serv')
mf_log = app_log.getChild('main')

MODULE_SCRIPTS_PATH = ModuleConfig.MODULE_SCRIPTS_PATH
MODULE_OUTPUT_PATH = ModuleConfig.MODULE_OUTPUT_FILES_PATH
DB_SCHEMA_INPUT_DATA = DBConfig.SchemasConfig.DB_SCHEMA_INPUT_DATA
DB_SCHEMA_REPORTS = DBConfig.SchemasConfig.DB_SCHEMA_REPORTS
DB_SCHEMA_REFERENCES = DBConfig.SchemasConfig.DB_SCHEMA_REFERENCES
DB_SCHEMA_SANDBOX = DBConfig.SchemasConfig.DB_SCHEMA_SANDBOX

PROJ_PARAM = AppConfig.PROJ_PARAM

pass_errors = False # параметр, влияющий на то будет ли падать модуль от ошибок.

refs_updated = False # указатель, обновлены ли за текущий запуск справочники

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

def update_ref(ref_name:str, config: dict, connection):
    filename = get_param(None, config, ['filename']) 
    header_size = get_param(None, config, ['header'])
    code_col = get_param(None, config, ['cd_col'])
    name_col = get_param(None, config, ['name_col'])
    read_ref_model = RefReadModel(filename=filename, sheet_name='ref', header=header_size)
    errors: list[dict] = []
    try:
        ref_df: pd.DataFrame = read_ref(read_ref_model)
    except Exception as e:
        raise e
    recieved_cols = list(ref_df.columns)
    if code_col not in recieved_cols:
        errors.append({'by_check': 'code col', 'message': f'code col "{code_col}" not in ref_df columns: {recieved_cols}'})
    if name_col not in recieved_cols:
        errors.append({'by_check': 'name col', 'message': f'name col "{name_col}" not in ref_df columns: {recieved_cols}'})
    if len(errors)>0:
        errors_str = ''
        for i, err in enumerate(errors, 1):
            errors_str+=f'\n{i}. Error while check {err["by_check"]}: {err["message"]}'
        _ex = f'Errors while update ref {ref_name}:{errors_str}'
        mf_log.error(_ex)
        raise KeyError(_ex)
    mf_log.info(f'Started upload {ref_name} to "{DB_SCHEMA_REFERENCES}"."{ref_name}"')
    ref_df.to_sql(name=ref_name, 
                  con=connection, 
                  schema=DB_SCHEMA_REFERENCES, 
                  index=False, 
                  if_exists='replace')
    

@timer
def start_calc(item: GeneralInfo):
    global refs_updated
    CURRENT_DATETIME = datetime.now()
    CURRENT_DATETIME_STR = CURRENT_DATETIME.strftime("%Y_%m_%d_%H_%M_%S")
    DB_CONNECTION_ROW = get_connection_row()

    calc_id = item.calc_id
    report_date = item.report_date
    report_date_fmt = calc_date_fmts[int(calc_id)]['report_date_fmt']
    prev_report_date = item.prev_report_date
    prev_report_date_fmt = calc_date_fmts[int(calc_id)]['prev_report_date_fmt']
    actual_date = item.actual_date
    actual_date_fmt = calc_date_fmts[int(calc_id)]['actual_date_fmt']

    mf_log.info(f'Started task: (calc_id={calc_id}, report_date={report_date}, prev_report_date={prev_report_date}, actual_date={actual_date})')
    
    _status = CalcStatus(
        percent=1,
        status="in_progress",
        message="started",
        calc_id=calc_id
    )

    # тест подключения к бд
    if module_db_tests.check_connection_status() == "not connected":
        _status._upd(None, "error", "db connection does not exists", calc_id)
        return _status.get_dict_status()

    reports_config_data = read_configuration_file(PROJ_PARAM)
    
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
            update_ref(ref_name=ref_name, 
                       config=ref_config, 
                       connection=DB_CONNECTION_ROW)
        refs_updated = True # справочники обновлены при первом запуске
    
    percents_remain = 100 - _status.percent
    percents_per_rep = (percents_remain) // len(activated_reports)
    for rep in activated_reports:
        
        rlog = mf_log.getChild(rep)
        rlog.info(f"Started report {rep}")

        dt_report_date = sql_variable(rep, SQL_VAR.VARIABLE)(datetime.strptime(report_date, report_date_fmt).date())
        dt_prev_report_date = sql_variable(rep, SQL_VAR.VARIABLE)(datetime.strptime(prev_report_date, prev_report_date_fmt).date())

        # чтение конфигурации этого отчета
        rep_config = get_param(None, reports_config.configuration_data_dict, ['reports', rep])
        mart_config = get_param(None, rep_config, ['mart_structure'])

        
        # обновление необходимых справочников, если еще не производили
        if not refs_updated:
            required_refs: list[str] = get_param([], mart_config, ['using_refs'])
            rlog.info(f'Started update required refs: {required_refs}')
            for ref_name in required_refs:
                ref_config = get_param(None, refs_configuration, ref_name)
                update_ref(ref_name=ref_name, 
                           config=ref_config, 
                           connection=DB_CONNECTION_ROW)


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
        rlog.debug(f'constructor:\n{constructor_df}')
        
        # получение уникальных метрик из конструктора
        calc_formula_constructor_col = constructor_df['calc_formula'].astype(str) # столбец с указанием из каких показателей состоит показатель
        unique_used_metrics:list[str] = []
        for metrics_in_row in calc_formula_constructor_col:
            list_row_metrics: list[str] = metrics_in_row.split(",")
            for metric in list_row_metrics:
                metric = metric.strip()
                try:
                    int(metric)
                    rlog.debug(f'Found number: {metric}')
                    continue
                except:
                    pass
                if metric not in unique_used_metrics:
                    rlog.debug(f'Found new param to calc: {metric}')
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
        group_results_cols_list = ", ".join(group_results_cols_list) if len(group_results_cols_list) > 0 else 'NOT FOUND COLS' # достижимо, если в конфигурации источника не указано ни одной колонки
        group_results_cols_list = sql_variable(rep, SQL_VAR.STRUCTURE)(group_results_cols_list)
        select_group_results_query = prepare_query(select_group_results_script, sql_variables[rep])
        rlog.info(f'Started get group results: \n{select_group_results_query}')
        results_by_groups = pd.read_sql(select_group_results_query, con=DB_CONNECTION_ROW)
        rlog.debug(f'results by groups:\n{results_by_groups}')
        if len(results_by_groups.index) == 0:
            _ex = f'Recieved results by groups len is 0. Further calculations dont make sense.'
            raise Exception(_ex)

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

        group_attrs_cols_list = ", ".join(group_attrs_cols_list) if len(group_attrs_cols_list) > 0 else 'NOT FOUND COLS' # достижимо, если в конфигурации источника не указано ни одной колонки
        group_attrs_cols_list = sql_variable(rep, SQL_VAR.STRUCTURE)(group_attrs_cols_list)
        
        group_attr_source_table_name = sql_variable(rep, SQL_VAR.VARIABLE)(rep_group_attrs_source_name)

        additional_group_attrs_columns_list:dict[str, str] =  get_param({}, group_attrs_source_config, ['additional_columns'])
        if len(additional_group_attrs_columns_list) > 0:
            _res_script = ', '
            _res_script = _res_script + ', '.join([f'{_add_col_assign} as {_add_col_name}' for _add_col_name, _add_col_assign in additional_group_attrs_columns_list.items()])
        else:
            _res_script = ''
        additional_group_attrs_cols_assign_script = sql_variable(rep, SQL_VAR.STRUCTURE)(_res_script)

        select_group_attrs_query = prepare_query(select_group_attrs_script, sql_variables[rep])
        rlog.info(f'Started get group attrs: \n{select_group_attrs_query}')
        group_attrs = pd.read_sql(select_group_attrs_query, con=DB_CONNECTION_ROW)
        rlog.debug(f'group attrs:\n{group_attrs}')
        if len(group_attrs.index) == 0:
            _ex = f'Recieved group attrs len is 0. Further calculations dont make sense.'
            raise Exception(_ex)
        
        groups_to_calc = group_attrs[get_param(None, group_attrs_source_config, 'primary_key_columns')].drop_duplicates() # уникальные группы из источника
        groups_to_calc = (
            groups_to_calc[groups_to_calc['calc_id'] == calc_id]
            .drop(columns=['calc_id'])
        )
        rlog.debug(f'groups_to_calc:\n{groups_to_calc}')

        amount_amt_group_results_columns = get_param(None, group_results_source_config, 'amount_columns')
        primary_key_group_results_columns = get_param(None, group_results_source_config, 'primary_key_columns')
        results_for_groups_to_calc = results_by_groups[primary_key_group_results_columns + amount_amt_group_results_columns]
        results_for_groups_to_calc = (
            results_for_groups_to_calc[results_for_groups_to_calc['calc_id'] == calc_id]
            .drop(columns=['calc_id'])
        )
        rlog.debug(f'results_for_groups_to_calc:\n{results_for_groups_to_calc}')

        metrics_to_calc_from_constr = constructor_df['metric_name'].drop_duplicates().astype(str) # уникальные названия показателей для расчета

        metrics_by_groups = {}
        for index, group_row in groups_to_calc.iterrows():
            group_id = group_row['group_id']
            rlog.info(f'{index+1}. Started calc group "{group_id}"')

            current_group_results:pd.DataFrame = results_for_groups_to_calc[results_for_groups_to_calc['group_id'] == group_id].drop(columns=['group_id'])
            rlog.debug(f'current_group_results:\n{current_group_results}')
            metrics_by_groups[group_id] = {}
            for metr in  metrics_to_calc_from_constr:
                calc_formula = constructor_df[constructor_df['metric_name'] == metr]['calc_formula'].iloc[0]
                metr_value = 0
                if calc_formula != "0" and calc_formula != 0:
                    rlog.debug(f'Calc_formula for "{metr}" from constructor: {calc_formula}')
                    calc_formula_used_params = [p.strip() for p in calc_formula.split(",")]
                    calc_formula_used_params_values = {}
                    for param in calc_formula_used_params:
                        filtered = current_group_results[current_group_results['amount_type_cd']==param][amount_amt_group_results_columns]
                        if not filtered.empty:
                            value = filtered.iloc(0)[0]
                        else:
                            _ex = f"No data found for amount_type_cd: {param}."
                            if pass_errors == True:
                                value = 0
                                _ex += f"It will be equal to {value}."
                                rlog.error(_ex)
                            else:
                                raise Exception(_ex)
                        calc_formula_used_params_values[param] = float(value)
                        rlog.debug(f'{param} = {calc_formula_used_params_values[param]}')
                    aggregated_value = 0
                    for param, param_val in calc_formula_used_params_values.items():
                        aggregated_value += param_val
                    rlog.debug(f'Aggregated {metr} value = {aggregated_value}')
                    metr_value = aggregated_value
                metrics_by_groups[group_id][metr] = metr_value
        calculated_metrics_df = (
            pd.DataFrame.from_dict(metrics_by_groups, orient='index')
            .reset_index()
            .rename(columns={'index': 'group_id'})
            )
        calculated_metrics_df = (
            calculated_metrics_df
            .melt(id_vars=['group_id'],
                  value_vars=[col for col in calculated_metrics_df.columns if col not in ['group_id']],
                  var_name='amount_type_cd',
                  value_name='amount_amt'
                  )
        )
        rlog.debug(f'calculated metrics:\n{calculated_metrics_df}')
        
        # сборка итогового dataframe со всеми необходимыми столбцами
        
        mart_df = (
            calculated_metrics_df
            .merge(group_attrs, how='left', on='group_id')
            .assign(report_date=lambda x: dt_report_date)
            .assign(prev_report_date=lambda x: dt_prev_report_date)
            .assign(load_dttm=lambda x: CURRENT_DATETIME)
        )
        mart_df['report_date'] = mart_df['report_date'].astype('date64[pyarrow]')
        mart_df['prev_report_date'] = mart_df['prev_report_date'].astype('date64[pyarrow]')
        mart_df['load_dttm'] = mart_df['load_dttm'].astype('datetime64[ns]')
        rlog.info(f'mart:\n{mart_df}')

        # временное сохранение полученной mart в output_files
        with pd.ExcelWriter(Path(create_path_if_not_exists(Path(MODULE_OUTPUT_PATH, PROJ_PARAM, rep)), f'{rep}__CALC_ID_{calc_id}__REP_DATE_{report_date}__CDTTM_{CURRENT_DATETIME_STR}.xlsx')) as writer:
            mart_df.to_excel(writer, sheet_name=f"temp_mart")
        
        # подготовка таблицы под витрину
        data_mart_name = sql_variable(rep, SQL_VAR.VARIABLE)(get_param(None, mart_config, 'table_name'))
        cols_configuration_from_json = get_param({}, reports_config.configuration_data_dict, ['cols_configuration'])
        configurated_cols = [k for k,v in cols_configuration_from_json.items()]
        def get_col_type(col_name: str):
            if col_name not in configurated_cols:
                return 'varchar'
            else:
                match cols_configuration_from_json[col_name]:
                    case "str":
                        return "varchar"
                    case "int":
                        return 'int'
                    case "float":
                        return 'numeric'
                    case "date":
                        return 'date'
                    case "datetime":
                        return 'timestamp'
                    case _:
                        return 'varchar'
        cols_to_be_in_mart = get_param(None, mart_config, 'columns')
        _cols_to_be_in_mart_script_parts = []
        try:
            for col_to_be_in_mart in cols_to_be_in_mart:
                _cols_to_be_in_mart_script_parts.append(f'{col_to_be_in_mart} {get_col_type(col_to_be_in_mart)}')
        except Exception as e:
            raise e
        cols_to_be_in_mart_with_types_script = sql_variable(rep, SQL_VAR.STRUCTURE)(', '.join(_cols_to_be_in_mart_script_parts))

        prepare_data_mart_table_script = open(Path(MODULE_SCRIPTS_PATH, 'prepare_data_mart_table.sql'),'r').read()
        
        
        rlog.info('Started data mart tests')
        mart_table_exists = module_db_tests.table_exists_test(schema_name=DB_SCHEMA_REPORTS, table_name=data_mart_name, conn_str=DB_CONNECTION_ROW)
        if mart_table_exists == 'ok':
            mart_columns_not_exists = module_db_tests.cols_exists_test(schema_name=DB_SCHEMA_REPORTS, table_name=data_mart_name,
                                                                   cols=cols_to_be_in_mart, conn_str=DB_CONNECTION_ROW)
            if len(mart_columns_not_exists)>0:
                _ex = f'Mart table exists, but it dont contains all requested cols: {cols_to_be_in_mart}\nResolve this error and retry.'
                rlog.error(_ex)
                raise Exception(_ex)
            else:
                rlog.info(f'Mart table exists and contain all required cols.')
        else:
            rlog.info('Mart table dont exists.')
            prepare_data_mart_table_query = prepare_query(prepare_data_mart_table_script, sql_variables[rep])
            rlog.info(f'Started prepare-data-mart-table query execute:\n{prepare_data_mart_table_query}')
            execute_query(prepare_data_mart_table_query, DB_CONNECTION_ROW)


        # # подключение справочников к dataframe с mart
        # получение всех справочников
        rlog.info(f'Started get required refs ({required_refs}) for mapping to mart.')
        refs = {}
        for ref in required_refs:
            refs[ref] = {}
            rlog.debug(f'started get {ref}')
            ref_table_name = sql_variable(ref, SQL_VAR.VARIABLE)(ref)
            db_schema_ref = sql_variable(ref, SQL_VAR.VARIABLE)(DB_SCHEMA_REFERENCES)
            cd_col = get_param(None, refs_configuration, [ref, 'cd_col'])
            name_col = get_param(None, refs_configuration, [ref, 'name_col'])
            cols_to_mapping_list = [cd_col, name_col]
            ref_cols_to_mapping_list = sql_variable(ref, SQL_VAR.STRUCTURE)(','.join(cols_to_mapping_list))
            make_where_cond = get_param(False, refs_configuration, [ref, 'where_condition'])
            
            condition_to_select = sql_variable(ref, SQL_VAR.FLAG)(True if make_where_cond != False else False)

            actual_date = sql_variable(ref, SQL_VAR.VARIABLE)(actual_date)

            if condition_to_select:
                where_condition_to_select_ref_to_mapping = sql_variable(ref, SQL_VAR.STRUCTURE)(make_where_cond)

            select_ref_df_script = open(Path(MODULE_SCRIPTS_PATH, 'subqueries', 'select_ref_to_mapping.sql'), 'r').read()
            rlog.info(f'started prepare query to select {ref}')
            select_ref_df_query = prepare_query(select_ref_df_script, sql_variables[ref])
            rlog.debug(f'executing query:\n{select_ref_df_query}')
            try:
                ref_df = pd.read_sql(sql=select_ref_df_query, con=DB_CONNECTION_ROW)
            except Exception as e:
                rlog.exception(e)
                raise
            rlog.debug(f'successfully recieved needed table.')
            refs[ref]['df'] = ref_df
            refs[ref]['cd_col'] = cd_col
            refs[ref]['name_col'] = name_col
        beautiful_mart_df = (
                mart_df.copy()
                )
        for ref_name, ref_data in refs.items():
            rlog.info(f'Started merge mart with {ref_name}.')
            cd_col = ref_data['cd_col']
            name_col = ref_data['name_col']
            ref_df = ref_data['df']
            try:
                beautiful_mart_df = (
                    beautiful_mart_df
                    .merge(ref_df, how='left', on=cd_col)
                )
            except Exception as e:
                rlog.exception(f'Error! Merge cant be applied to data mart.')
                raise
        # временное сохранение полученной mart в output_files
        with pd.ExcelWriter(Path(create_path_if_not_exists(Path(MODULE_OUTPUT_PATH, PROJ_PARAM, rep)), f'{rep}__CALC_ID_{calc_id}__REP_DATE_{report_date}__CDTTM_{CURRENT_DATETIME_STR}.xlsx'), mode='a') as writer:
            beautiful_mart_df.to_excel(writer, sheet_name=f"fully_merged_mart")
        rlog.info(f'Started construct result mart {rep}')
        try:
            beautiful_mart_df = beautiful_mart_df[cols_to_be_in_mart]
        except Exception as e:
            rlog.exception(f'Error! Mart dont contains requested cols ({cols_to_be_in_mart}): {list(beautiful_mart_df.columns)}')
            raise
        rlog.debug(f'successful constructed result mart:\n{beautiful_mart_df}')
        
        # временное сохранение полученной mart в output_files
        with pd.ExcelWriter(Path(create_path_if_not_exists(Path(MODULE_OUTPUT_PATH, PROJ_PARAM, rep)), f'{rep}__CALC_ID_{calc_id}__REP_DATE_{report_date}__CDTTM_{CURRENT_DATETIME_STR}.xlsx'), mode='a') as writer:
            beautiful_mart_df.to_excel(writer, sheet_name=f"result_mart")
        
        
        _com = """
    другой парсер формул:
    split по "and" -> strip -> имеем действия по три. 
    записываем полученные действия в dict (например, and_dict)
    для каждого действия (или если есть значения во временном dict с промежуточными результатами)
        split по " " -> strip -> имеем список [столбец/значение, оператор, столбец/значение].
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
        
        # manual_sleep(seconds=30)
        rlog.info(f'Succsessful generated {rep} report.')
        _status._upd(_status.percent + percents_per_rep, "in progress", f"processing report {rep}", calc_id)

    mf_log.info(f'Succesful end of generatig reports ({activated_reports}): {item}')

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