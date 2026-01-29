import ast
import operator as op

# Whitelist of allowed operators
allowed_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg
}

def safe_eval(expr):
    """
    Safely evaluates a string expression using a whitelist of operators.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError, ValueError, NameError):
        return "Error"

def _eval_node(node):
    """
    Recursively evaluates an AST node.
    """
    if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num is for older Python versions
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        operator = allowed_operators.get(type(node.op))
        if operator is None:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return operator(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        operator = allowed_operators.get(type(node.op))
        if operator is None:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return operator(operand)
    else:
        raise TypeError(f"Unsupported node type: {type(node).__name__}")
