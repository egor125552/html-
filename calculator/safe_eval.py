import ast
import operator as op

# Поддерживаемые операторы
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg
}

def safe_eval(expr):
    """
    Безопасно вычисляет математическое выражение.
    """
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError):
        return "Ошибка"

def _eval(node):
    """
    Рекурсивно вычисляет узел AST.
    """
    if isinstance(node, ast.Constant): # Python 3.8+
        return node.n
    elif isinstance(node, ast.Num): # для совместимости
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(node)
