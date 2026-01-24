import ast
import operator as op

# Supported operators
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
    Safely evaluates a string expression using a whitelist of AST nodes.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError, ValueError) as e:
        # Return error messages for specific exceptions
        if isinstance(e, ZeroDivisionError):
            return "Деление на ноль"
        return "Ошибка ввода"

def _eval_node(node):
    """
    Recursively evaluates an AST node.
    """
    # For Python 3.8+ compatibility (ast.Constant)
    if isinstance(node, ast.Constant):
        return node.value
    # For older Python versions (ast.Num)
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in operators:
            raise TypeError(f"Unsupported operator: {type(node.op)}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in operators:
            raise TypeError(f"Unsupported operator: {type(node.op)}")
        operand = _eval_node(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError(f"Unsupported node type: {type(node)}")

# Example usage (for testing)
if __name__ == '__main__':
    print(safe_eval("2 + 2 * 3"))
    print(safe_eval("10 / 2"))
    print(safe_eval("2^8"))
    print(safe_eval("10 / 0"))
    print(safe_eval("-5 + 10"))
    print(safe_eval("__import__('os').system('echo pwned')"))
