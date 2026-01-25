import ast
import operator as op

# Whitelist of allowed operations: mapping AST nodes to operator functions.
_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv, # Use truediv for float division
    ast.USub: op.neg,    # Unary minus (negative numbers)
}

def _eval_node(node):
    """
    Recursively evaluates a single AST node.
    This function handles numbers, unary operations, and whitelisted binary operations.
    """
    # ast.Num is for older Python versions, ast.Constant for 3.8+
    if isinstance(node, (ast.Num, ast.Constant)):
        # The value is in 'n' for Num and 'value' for Constant
        return node.n if isinstance(node, ast.Num) else node.value

    elif isinstance(node, ast.BinOp):
        # Check if the operator is in our whitelist
        if type(node.op) not in _ALLOWED_OPS:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")

        # Get the corresponding operator function
        op_func = _ALLOWED_OPS[type(node.op)]

        # Recursively evaluate the left and right operands
        left_val = _eval_node(node.left)
        right_val = _eval_node(node.right)

        return op_func(left_val, right_val)

    elif isinstance(node, ast.UnaryOp):
        # Handle unary operations (e.g., negation)
        if type(node.op) not in _ALLOWED_OPS:
            raise TypeError(f"Unsupported unary operator: {type(node.op).__name__}")

        op_func = _ALLOWED_OPS[type(node.op)]
        operand_val = _eval_node(node.operand)
        return op_func(operand_val)

    else:
        # If the node type is anything else, it's not supported.
        raise TypeError(f"Unsupported node type: {type(node).__name__}")


def safe_eval(expression):
    """
    Safely evaluates a mathematical expression string using an AST traversal.

    Args:
        expression: A string containing a simple mathematical expression.

    Returns:
        The numerical result of the expression, or an error message string.
    """
    if not isinstance(expression, str) or not expression:
        return "Error"

    try:
        # Parse the expression into an AST. 'eval' mode means a single expression is expected.
        node = ast.parse(expression, mode='eval').body
        return _eval_node(node)
    except ZeroDivisionError:
        return "Error"
    except (SyntaxError, TypeError, ValueError, KeyError):
        # If parsing or evaluation fails, return a generic error message.
        return "Error"
