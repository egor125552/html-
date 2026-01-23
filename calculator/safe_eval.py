import ast
import operator as op

# Разрешенные операторы
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg
}

def safe_eval(expression):
    """
    Безопасно вычисляет математическое выражение.
    Поддерживает: сложение, вычитание, умножение, деление,
    возведение в степень и унарный минус.
    """
    try:
        node = ast.parse(expression, mode='eval').body
        return _eval_node(node)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError) as e:
        # Возвращаем строку с ошибкой для отображения в калькуляторе
        if isinstance(e, ZeroDivisionError):
            return "Деление на ноль"
        return "Ошибка ввода"

def _eval_node(node):
    """Рекурсивно вычисляет значение узла AST."""
    if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num для старых версий Python
        return node.n
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in operators:
            raise TypeError(f"Неподдерживаемый оператор: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in operators:
            raise TypeError(f"Неподдерживаемый оператор: {type(node.op).__name__}")
        operand = _eval_node(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(f"Неподдерживаемый узел: {type(node).__name__}")
