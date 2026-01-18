import ast
import operator as op

# Разрешённые операции
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Безопасно вычисляет математическое выражение, используя AST.
    """
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError):
        return "Ошибка"

def _eval_node(node):
    """
    Рекурсивно вычисляет значение узла AST.
    """
    if isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    if isinstance(node, ast.Constant):  # Python >= 3.8
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(f"Неподдерживаемый узел: {type(node).__name__}")
