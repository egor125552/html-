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

    def evaluate(self, expression):
        try:
            # Replace visual symbols with python compatible ones if necessary
            # Though main.py should probably handle the translation to python-evaluable string
            node = ast.parse(expression, mode='eval').body
            return self._eval(node)
        except Exception:
            return "Error"

    def _eval(self, node):
        if isinstance(node, (ast.Constant, ast.Num)):
            if isinstance(node, ast.Constant):
                return node.value
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            return self.operators[type(node.op)](operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.functions:
                args = [self._eval(arg) for arg in node.args]
                return self.functions[func_name](*args)
            raise ValueError(f"Function {func_name} not supported")
        elif isinstance(node, ast.Name):
            if node.id in self.constants:
                return self.constants[node.id]
            raise ValueError(f"Constant {node.id} not supported")
        else:
            raise TypeError(f"Unsupported node type {type(node)}")

def safe_eval(expression):
    return SafeEval().evaluate(expression)
