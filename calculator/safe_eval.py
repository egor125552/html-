import ast
import math

def safe_eval(expr):
    """
    Safely evaluate a mathematical expression using AST.
    Supports basic arithmetic, power, and common math functions.
    """
    # Replace '^' with '**' for Python compatibility
    expr = expr.replace('^', '**')

    # Whitelist of allowed operators and functions
    allowed_operators = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: a,
    }

    allowed_functions = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'log': math.log,
        'exp': math.exp,
    }

    allowed_names = {
        'pi': math.pi,
        'e': math.e,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        # Backward compatibility for older Python versions
        try:
            if isinstance(node, ast.Num):
                return node.n
        except AttributeError:
            pass

        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            return allowed_operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            return allowed_operators[type(node.op)](operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                args = [_eval(arg) for arg in node.args]
                return allowed_functions[node.func.id](*args)
            raise ValueError(f"Function {node.func} not allowed")
        elif isinstance(node, ast.Name):
            if node.id in allowed_names:
                return allowed_names[node.id]
            raise ValueError(f"Name {node.id} not allowed")
        elif isinstance(node, ast.Expression):
            return _eval(node.body)
        else:
            raise TypeError(f"Unsupported expression node: {type(node)}")

    try:
        tree = ast.parse(expr, mode='eval')
        result = _eval(tree.body)
        # Handle cases where result is a float that could be an int
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except Exception:
        return "Error"
