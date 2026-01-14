import ast
import operator as op

# Белый список разрешенных операторов
allowed_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg, # Для унарного минуса (отрицательные числа)
}

def safe_eval(expr):
    """
    Безопасно вычисляет строку с математическим выражением.
    Разрешает только базовые арифметические операции.
    """
    if not expr:
        return 0.0
    try:
        # Разбираем строку в AST-дерево
        node = ast.parse(expr, mode='eval').body
    except (SyntaxError, ValueError):
        raise ValueError("Некорректный синтаксис")

    # Рекурсивно вычисляем значение узла
    return _eval_node(node)

def _eval_node(node):
    """
    Рекурсивно вычисляет узел AST.
    """
    # Для чисел (ast.Num для старых версий Python, ast.Constant для новых)
    if isinstance(node, (ast.Constant, ast.Num)):
        return float(node.n)

    # Для бинарных операций (+, -, *, /)
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in allowed_operators:
            raise ValueError(f"Оператор не разрешен: {op_type.__name__}")

        left_val = _eval_node(node.left)
        right_val = _eval_node(node.right)

        # Проверка деления на ноль
        if isinstance(node.op, ast.Div) and right_val == 0:
            raise ZeroDivisionError("Деление на ноль")

        return allowed_operators[op_type](left_val, right_val)

    # Для унарных операций (например, -5)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in allowed_operators:
            raise ValueError(f"Оператор не разрешен: {op_type.__name__}")

        operand_val = _eval_node(node.operand)
        return allowed_operators[op_type](operand_val)

    # Все остальные типы узлов запрещены
    else:
        raise TypeError(f"Тип узла не разрешен: {type(node).__name__}")
