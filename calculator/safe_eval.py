import ast
import operator as op

# Whitelist of allowed AST node types
allowed_nodes = {
    ast.Expression,
    ast.Constant,  # For Python 3.8+
    ast.Num,       # For older Python versions
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.USub,
}

# Whitelist of operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def _eval_node(node):
    """Recursively evaluate a single AST node."""
    node_type = type(node)

    if node_type not in allowed_nodes:
        # Check if it's a whitelisted operator type
        is_operator = any(isinstance(node, op_type) for op_type in operators)
        if not is_operator:
            raise TypeError(f"Unsupported node type: {node_type.__name__}")

    if isinstance(node, (ast.Constant)):
        return node.value
    elif isinstance(node, (ast.Num)): # For older python versions
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        operator_func = operators.get(type(node.op))
        if operator_func is None:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return operator_func(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        operator_func = operators.get(type(node.op))
        if operator_func is None:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return operator_func(operand)
    elif isinstance(node, ast.Expression):
        return _eval_node(node.body)
    else:
        # This part should not be reached if the node type is in allowed_nodes
        # but provides a fallback for operator types like ast.Add, etc.
        if type(node) in operators:
            return operators[type(node)]
        else:
            raise TypeError(f"Unsupported node type: {type(node).__name__}")


def safe_eval(expr):
    """
    Safely evaluates a string containing a mathematical expression.
    """
    if not isinstance(expr, str):
        return "Error"
    try:
        # Replace user-friendly operators with standard ones for parsing
        expr = expr.replace('×', '*').replace('÷', '/')
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree)
    except (SyntaxError, TypeError, ZeroDivisionError, ValueError, KeyError, RecursionError):
        return "Error"
