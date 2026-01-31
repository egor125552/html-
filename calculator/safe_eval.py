import ast
import math
import operator

# Allowed operations
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# Allowed functions and constants
MATH_FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sqrt': math.sqrt,
    'log': math.log,
    'exp': math.exp,
}

MATH_CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
}

def safe_eval(expression):
    """
    Safely evaluate a mathematical expression using AST.
    """
    if not expression:
        return ""

    # Replace visual symbols with python operators
    expression = expression.replace('×', '*').replace('÷', '/')

    try:
        node = ast.parse(expression, mode='eval').body
        result = _eval(node)
        # Format result: if it's an integer, show it as an integer
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception:
        return "Error"

def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval(node.left)
        right = _eval(node.right)
        return OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand)
        return OPERATORS[type(node.op)](operand)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in MATH_FUNCTIONS:
                args = [_eval(arg) for arg in node.args]
                return MATH_FUNCTIONS[func_name](*args)
        raise ValueError("Function call not allowed")
    elif isinstance(node, ast.Name):
        if node.id in MATH_CONSTANTS:
            return MATH_CONSTANTS[node.id]
        raise ValueError(f"Name {node.id} is not allowed")
    # ast.Num is deprecated and replaced by ast.Constant in newer Python
    elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
        return node.n
    else:
        raise TypeError(f"Unsupported node type: {type(node)}")
