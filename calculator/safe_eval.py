import ast
import operator as op

# Разрешенные операции
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg
}

def safe_eval(expr):
    """
    Безопасно вычисляет математическое выражение, используя ast.
    """
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    except ZeroDivisionError:
        return "Деление на ноль"
    except (TypeError, SyntaxError, KeyError):
        return "Ошибка ввода"

def _eval(node):
    """
    Рекурсивно вычисляет узел AST.
    """
    if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num для обратной совместимости
        return node.n
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in operators:
            raise TypeError(node.op)
        left = _eval(node.left)
        right = _eval(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in operators:
            raise TypeError(node.op)
        operand = _eval(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(node)
