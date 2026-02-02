import ast
import operator
import math

class SafeEval:
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        self.functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'exp': math.exp,
            'factorial': math.factorial,
        }
        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }

    def eval(self, expr):
        if not expr:
            return ""
        try:
            # Replace common symbols with Python-compatible ones
            # Using _ for negative sign if it's used in UI to distinguish from subtraction
            clean_expr = expr.replace('×', '*').replace('÷', '/').replace('^', '**')
            node = ast.parse(clean_expr, mode='eval').body
            result = self._eval(node)
            if isinstance(result, float) and result.is_integer():
                return int(result)
            return result
        except ZeroDivisionError:
            return "Error: Div by 0"
        except Exception as e:
            return f"Error"

    def _eval(self, node):
        if isinstance(node, (ast.Constant, getattr(ast, 'Num', ast.Constant))):
            return getattr(node, 'value', getattr(node, 'n', None))
        elif isinstance(node, ast.BinOp):
            return self.operators[type(node.op)](self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return self.operators[type(node.op)](self._eval(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.functions:
                args = [self._eval(arg) for arg in node.args]
                return self.functions[func_name](*args)
            raise NameError(f"Unsupported function: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in self.constants:
                return self.constants[node.id]
            raise NameError(f"Unsupported constant: {node.id}")
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

def safe_eval(expr):
    return SafeEval().eval(expr)
