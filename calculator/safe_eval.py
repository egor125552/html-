import ast
import math
import operator

class SafeEval:
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
        }

        self.functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'factorial': math.factorial,
            'exp': math.exp,
            'abs': abs,
        }

        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }

    def eval(self, expr):
        if not expr:
            return ""
        try:
            # Replace visual symbols with Python equivalents before parsing
            clean_expr = expr.replace('×', '*').replace('÷', '/')
            node = ast.parse(clean_expr, mode='eval').body
            result = self._eval(node)
            # Round to 10 decimal places to avoid float precision issues
            if isinstance(result, float):
                result = round(result, 10)
                # Convert to int if it's a whole number
                if result.is_integer():
                    result = int(result)
            return result
        except Exception:
            return "Error"

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            return self.operators[type(node.op)](operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise TypeError("Only direct function calls are supported")
            func_name = node.func.id
            if func_name not in self.functions:
                raise NameError(f"Function {func_name} is not supported")
            args = [self._eval(arg) for arg in node.args]
            return self.functions[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id not in self.constants:
                raise NameError(f"Constant {node.id} is not supported")
            return self.constants[node.id]
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

def safe_eval(expr):
    return SafeEval().eval(expr)
