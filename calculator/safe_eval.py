import ast
import operator as op

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.UAdd: lambda x: x,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Safely evaluates a string expression using a whitelist of AST nodes.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except (SyntaxError, ValueError, TypeError):
        raise ValueError("Invalid expression")

def _eval_node(node):
    """
    Recursively evaluates an AST node.
    """
    if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num is for older Python versions
        # In Python 3.8, ast.Num is deprecated and replaced by ast.Constant
        if hasattr(node, 'value'):
            return node.value
        return node.n # For older versions
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in operators:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in operators:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        operand = _eval_node(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(f"Unsupported node type: {type(node).__name__}")
