import ast
import math

def safe_eval(expr):
    """
    Safely evaluate a mathematical expression using AST.
    """
    if not expr:
        return ""

    # Replace visual symbols with python operators if necessary
    # (though usually the UI handles this, it's good to be robust)
    expr = expr.replace('×', '*').replace('÷', '/')

    # Supported operators
    operators = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.Mod: lambda a, b: a % b,
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: a,
    }

    # Supported functions
    functions = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'log': math.log10,  # Common log
        'ln': math.log,     # Natural log
        'exp': math.exp,
        'factorial': math.factorial,
    }

    # Supported constants
    constants = {
        'pi': math.pi,
        'e': math.e,
    }

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_node(node.operand))
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            # Fallback for very old Python versions if needed
            return node.n
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in functions:
                args = [eval_node(arg) for arg in node.args]
                return functions[func_name](*args)
            raise ValueError(f"Function {func_name} is not supported")
        elif isinstance(node, ast.Name):
            if node.id in constants:
                return constants[node.id]
            raise ValueError(f"Constant {node.id} is not supported")
        else:
            raise TypeError(f"Unsupported node type: {type(node).__name__}")

    try:
        tree = ast.parse(expr, mode='eval')
        result = eval_node(tree)
        # Format result to avoid trailing .0 for integers
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except Exception:
        return "Error"
