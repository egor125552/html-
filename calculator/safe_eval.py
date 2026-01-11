import ast
import operator as op

# Разрешённые операторы
_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def _eval_node(node):
    """Рекурсивно вычисляет узел AST."""
    if isinstance(node, (ast.Constant, ast.Num)):
        return node.value if isinstance(node, ast.Constant) else node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        return _OPERATORS[type(node.op)](operand)
    else:
        raise TypeError(f"Неподдерживаемый тип узла: {type(node)}")

def safe_eval(expression: str):
    """Безопасно вычисляет математическое выражение."""
    try:
        # Преобразуем строку в AST-дерево
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        # Для единообразия всегда возвращаем float
        return float(result)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError, ValueError):
        return None
