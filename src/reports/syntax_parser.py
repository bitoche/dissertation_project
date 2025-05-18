from enum import Enum
import sys, re, inspect, logging as _logging
from itertools import chain
from collections import defaultdict
from ..handlers import timer, replace_all

logger = _logging.getLogger('serv').getChild('rep').getChild('parser')

class SQL_VAR(Enum):
    """
    :VARIABLE: обозначение = `&`, по смыслу - число, строка, дата, и тп
    :FLAG: обозначение = `$`, по смыслу - комментарий(`'--'`) при `False`, и ничего (`''`) при `True`
    :NEG_FLAG: обозначение = `!$`, по смыслу - обратное флагу. Автоматически создается при назначении обычного флага.
    :STRUCTURE: обозначение = `#`, по смыслу - строка - часть скрипта, в которой могут быть свои переменные. Проверяется рекурсивно.
    """
    VARIABLE = '&'
    FLAG = '$' # при true = '', при false = '--'
    NEG_FLAG = "!$" # при true = '--', при false = ''
    STRUCTURE = '#'

sql_variables = defaultdict(dict)

class SQLVariable:
    """
    ### Описание:
        Класс для авто-заполнения словаря переменных для sql-запросов.
    ### Применение:
        При объявлении переменной необходимо использовать конструкцию:
        ```python
        variable = sql_variable('отчет1', SQL_VAR.ТИП_ПЕРЕМЕННОЙ)('Значение переменной')
        ```
        , где:
            1. variable - название переменной в sql-запросе
            2. sql_variable - метод, создающий объект класса SQLVariable
            3. 'отчет1' - название отчета, а так же КЛЮЧ для общего словаря переменных.
            4. ТИП_ПЕРЕМЕННОЙ - тип переменной из класса SQL_VAR, который определяет знак перед переменной в запросе:
                - VARIABLE {SQL_VAR.VARIABLE.value} - Тип переменной, в которой хранится **значение** (str, int, float)
                - FLAG {SQL_VAR.FLAG.value}/{SQL_VAR.NEG_FLAG.value} - Тип переменной, которая *переключает* строки (значение True при присвоении заменяет значение переменной на '', а False на '--'. В случае использования ! - наоборот)
                - STRUCTURE {SQL_VAR.STRUCTURE.value} - Тип переменной, в которой хранится **структура** (при подготовке запроса такие переменные проверяются рекурсивно, заходя в value из dict.)
                5. 'Значение переменной' - любое значение, которое можно представить в текстовом виде (str())
        В итоге, эта переменная автоматически появляется в словаре sql_variables['отчет1'], и ее можно использовать в запросе, если запрос подготавливается с помощью `prepare_query`
    """
    def __init__(self, report_name, type: SQL_VAR):
        self.report_name = report_name
        self.type = type
    
    def __call__(self, value):
        
        # получение фрейма вызывающего кода
        frame = sys._getframe(1)
        
        # ищем строку с присваиванием в исходном коде
        lines = inspect.getframeinfo(frame).code_context
        if lines:
            line = lines[0].strip()
            if '=' in line:
                # извлекаем имя переменной слева от '='
                var_name = line.split('=')[0].strip()
                match self.type:
                    case SQL_VAR.FLAG:
                        # так как используются похожие конструкции - порядок сохранения важен. сначала ту, у которой есть "!"
                        sql_variables[self.report_name][f'{SQL_VAR.NEG_FLAG.value}{var_name}'] = '--' if value else ''
                        sql_variables[self.report_name][f'{SQL_VAR.FLAG.value}{var_name}'] = '' if value else '--'
                    case SQL_VAR.NEG_FLAG:
                        # надо ли добавлять флаг, если присвоили NEG_FLAG?
                        sql_variables[self.report_name][f'{SQL_VAR.NEG_FLAG.value}{var_name}'] = '--' if value else ''
                    case _:
                        sql_variables[self.report_name][f'{self.type.value}{var_name}'] = str(value)
        logger.debug(f'For variable {var_name} assigned value={value}')
        return value

def sql_variable(report_name, type: SQL_VAR):
    logger.debug(f'Added new variable with type={type.name} for {report_name} report')
    return SQLVariable(report_name, type)

def check_for_variable_availability(query: str, prepared_variables_dict: dict) -> tuple[bool, list[tuple[str, int]]]:
    """
    ### Принимает:
        - запрос в виде str
        - словарь переменных для замены
    ### Возвращает:
        Кортеж: 
            (True/False(все ли переменные найдены), 
            Список кортежей: [(ненайденная переменная/название подструктуры, номер строки/строки в подструктуре),...])
    """
    lines = query.split('\n')  # Разбиваем запрос на строки
    not_found_vars_with_line: list[tuple[str, int]] = []
    is_ready = True

    for line_num, line in enumerate(lines, start=1):  # Нумерация строк с 1
        inner_construction_matches = re.finditer(r'(#\w+)', line)
        for construction_match in inner_construction_matches:
            var_name = construction_match.group(1)
            if var_name not in prepared_variables_dict:
                is_ready = False
                not_found_vars_with_line.append((var_name, line_num))
            else:
                logger.info(f'Started inner-construction variables check for \"{var_name}\"')
                if var_name in prepared_variables_dict[var_name]:
                    raise RecursionError(f'Found recusion inclusion of a variable \"{var_name}\". Check the inner-construction.')
                inner_construction_check_result = check_for_variable_availability(prepared_variables_dict[var_name], prepared_variables_dict)
                if inner_construction_check_result[0] == False:
                    logger.info(f'Not found variables for inner-construction variable \"{var_name}\": {inner_construction_check_result[1]}')
                    not_found_vars_with_line.append((var_name, inner_construction_check_result[1]))
        # в идеале добавить сюда не хардкодовое значение, а через f'{SQL_VAR.<type>.value}'
        neg_flag_matchers = re.finditer(r'(\!\$\w+)', line)
        flag_matches = re.finditer(r'(\$\w+)', line)
        variable_matches = re.finditer(r'(&\w+)', line) 
        flag_and_variable_matches = chain(neg_flag_matchers, flag_matches, variable_matches)
        for match in flag_and_variable_matches:
            var_name = match.group(1)  # Полное совпадение (напр., "&calc_id")

            if var_name not in prepared_variables_dict:
                is_ready = False
                not_found_vars_with_line.append((var_name, line_num))

    return (is_ready, not_found_vars_with_line)

def check_for_variables(query):
    """
    ### Принимает:
        Запрос в виде str
    ### Возвращает:
        True/False (содержится ли в запросе хотя бы одна переменная вида из SQL_VAR)
    """
    for i, var_type in enumerate(SQL_VAR):
        if(var_type.value in query):
            return True
    return False

@timer
def prepare_query(query:str, prepared_variables_dict: dict, repeat = None):
    """
    ### Принимает:
        - Запрос в виде str
        - словарь замен (key - переменная)
        - необязательный параметр repeat (влияет только на лог-сообщения)
    ### Возвращает:
        - Запрос с замененными переменными по словарю замен
        - Ошибку, если в словаре не хватает некоторых переменных
    """
    logger.info(f'Started {"re-" if repeat else ""}prepare query')
    # start_time = time.perf_counter()
    is_all_variables_found, not_found_variables = check_for_variable_availability(query, prepared_variables_dict)
    if is_all_variables_found:
        ready_query = replace_all(query, prepared_variables_dict)
        if check_for_variables(ready_query) == False:
            logger.info(f'All variables in query are replaced.')
            # end_time = time.perf_counter()
            # logger.info(f'Elapsed time for preparing query is {end_time-start_time:.4f} sec.')
            return ready_query
        else:
            logger.info(f'Found uncompleted variable-replacements. Starting repeat call to prepare')
            return prepare_query(ready_query, prepared_variables_dict, True)
    else:
        str_not_found_variables = '\n'+'\n'.join([f'"{t[0]}" at line {t[1]}' for t in not_found_variables]) 
        query_by_lines = query.split('\n')
        lined_query = '\n'.join([f'{i+1}.\t{query_by_lines[i]}' for i in range(len(query_by_lines))])
        nf_vars_mess = f"Not found variables from query in prepared variables dict for this report: {str_not_found_variables}"
        # здесь можно для удобства добавить вывод того, что нашлось. со значениями (до определенной длины)
        beautiful_prep_var_dict = {}
        cut_value_len_to = 30
        for var,val in prepared_variables_dict.items():
            beautiful_prep_var_dict[var] = val[:cut_value_len_to]+'...' if len(val) > cut_value_len_to else val
        loc_vars_mess = f"\n-> Filled variables dict is: \n{beautiful_prep_var_dict}"
        raw_lined_query_mess = f"\n-> Query to prepare is:\n{lined_query}\n"
        ex = nf_vars_mess + loc_vars_mess + raw_lined_query_mess
        logger.exception(ex)
        raise ValueError('Not found variables from query in prepared variables dict for this report.')