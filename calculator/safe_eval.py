import ast
import operator as op

# Whitelist of allowed operators
allowed_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Safely evaluates a mathematical expression string.
    Only allows basic arithmetic operations.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except ZeroDivisionError:
        raise
    except (TypeError, SyntaxError, KeyError, ValueError) as e:
        raise ValueError(f"Invalid or unsupported expression: {e}")

def _eval_node(node):
    """
    Recursively evaluates an AST node.
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num): # For older Python versions
        return node.n
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in allowed_operators:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return allowed_operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in allowed_operators:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        operand = _eval_node(node.operand)
        return allowed_operators[type(node.op)](operand)
    else:
        raise ValueError(f"Unsupported node type: {type(node).__name__}")
