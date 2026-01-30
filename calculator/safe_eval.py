import ast
import operator
import math

# Map AST operators to operator functions
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.Pow: operator.pow,
}

# Allowed functions
_FUNCTIONS = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
}

def safe_eval(expression):
    """
    Safely evaluate a mathematical expression using AST.
    """
    try:
        # Replace visual operators with Python-friendly ones
        expression = expression.replace('×', '*').replace('÷', '/')
        expression = expression.replace('^', '**')
        expression = expression.replace('√', 'sqrt')
        expression = expression.replace('_', '-')

        node = ast.parse(expression, mode='eval').body
        return _eval_node(node)
    except Exception:
        return "Error"

def _eval_node(node):
    if isinstance(node, (ast.Constant, ast.Num)):
        if isinstance(node, ast.Num):
            return node.n
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            return _OPERATORS[op_type](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _OPERATORS:
            return _OPERATORS[op_type](_eval_node(node.operand))
    elif isinstance(node, ast.Name):
        if node.id in _FUNCTIONS:
            return _FUNCTIONS[node.id]
    elif isinstance(node, ast.Call):
        func = _eval_node(node.func)
        args = [_eval_node(arg) for arg in node.args]
        return func(*args)

    raise TypeError(f"Unsupported operation: {node}")
