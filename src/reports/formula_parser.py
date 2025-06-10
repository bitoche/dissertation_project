import ast
import re

# Класс для вычисления формулы через обход AST
class FormulaEvaluator(ast.NodeVisitor):
    def __init__(self):
        self.variables = {}

    # Обработка бинарных операций (+, -, *, / и т.д.)
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            return left / right
        elif isinstance(op, ast.BitXor):  # Поддержка XOR через ^
            if isinstance(left, bool) and isinstance(right, bool):
                return left != right
            return left ^ right
        raise ValueError(f"Unsupported operation: {op.__class__.__name__}")

    # Обработка сравнений (>, <, ==, != и т.д.)
    def visit_Compare(self, node):
        left = self.visit(node.left)
        for op, right_node in zip(node.ops, node.comparators):
            right = self.visit(right_node)
            if isinstance(op, ast.Gt):
                if left <= right:
                    return False
            elif isinstance(op, ast.Lt):
                if left >= right:
                    return False
            elif isinstance(op, ast.Eq):
                if left != right:
                    return False
            elif isinstance(op, ast.NotEq):
                if left == right:
                    return False
            elif isinstance(op, ast.GtE):
                if left < right:
                    return False
            elif isinstance(op, ast.LtE):
                if left > right:
                    return False
            left = right
        return True

    # Обработка логических операций (and, or)
    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            return all(self.visit(value) for value in node.values)
        elif isinstance(node.op, ast.Or):
            return any(self.visit(value) for value in node.values)
        raise ValueError(f"Unsupported logical operation: {node.op.__class__.__name__}")

    # Обработка унарных операций (not)
    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        raise ValueError(f"Unsupported unary operation: {node.op.__class__.__name__}")

    # Обработка переменных
    def visit_Name(self, node):
        name = node.id
        if name in self.variables:
            return self.variables[name]
        raise ValueError(f"Unknown variable: {name}")

    # Обработка констант (числа, строки и т.д.)
    def visit_Constant(self, node):
        return node.value

    # Метод для вычисления формулы
    def evaluate(self, formula, variables):
        self.variables = variables
        try:
            tree = ast.parse(formula, mode='eval')
            result = self.visit(tree.body)
            if not isinstance(result, bool):
                raise ValueError("Formula must return bool value")
            return result
        except SyntaxError as e:
            raise ValueError(f"Syntax error at formula: {e}")

# Функция для извлечения строковых значений из формулы
def extract_strings(formula, variables):
    def replacer(match):
        identifier = f"_str{len(variables)}"
        # Используем match.group(0) и удаляем кавычки
        variables[identifier] = match.group(0)[1:-1]
        return identifier
    # Регулярка для строк в одинарных или двойных кавычках
    pattern = r"'[^']*'|\"[^\"]*\""
    return re.sub(pattern, replacer, formula)

# Главный метод
def parse_formula(formula, one_line_df):
    """
    Вычисляет булево значение формулы на основе данных из DataFrame.
    
    Args:
        formula (str): Формула, например, "report_dt > '2025-01-01' and inception_dt < '2025-01-01'"
        df (pandas.DataFrame): DataFrame с одной строкой, где столбцы соответствуют переменным
        
    Returns:
        bool: Результат вычисления (True или False)
        
    Raises:
        ValueError: Если DataFrame не содержит одну строку или формула некорректна
    """
    if one_line_df.shape[0] != 1:
        raise ValueError("DataFrame must contains only one row")
    
    # Извлекаем значения из DataFrame в словарь
    variables = one_line_df.iloc[0].to_dict()
    
    # Обрабатываем строковые значения в формуле
    formula = extract_strings(formula, variables)
    
    # Создаем evaluator и вычисляем формулу
    evaluator = FormulaEvaluator()
    try:
        result = evaluator.evaluate(formula, variables)
        return result
    except Exception as e:
        raise ValueError(f"Error while parsing formula: {e}")