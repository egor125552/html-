import ast
import operator as op

# Допустимые операторы
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Безопасно вычисляет математическое выражение, используя AST.
    Поддерживает только числа и базовые арифметические операции.
    """
    try:
        # Устаревший ast.Num используется для совместимости со старыми версиями Python
        node = ast.parse(expr, mode='eval').body
        return _eval_node(node)
    except (TypeError, SyntaxError, KeyError, ZeroDivisionError, ValueError) as e:
        # Возвращаем сообщение об ошибке, если выражение некорректно
        return f"Ошибка: {e}"

def _eval_node(node):
    """Рекурсивно вычисляет значение узла AST."""
    if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num для старых версий Python
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        return operators[type(node.op)](operand)
    else:
        # Если узел не является разрешенным, вызываем ошибку
        raise TypeError(f"Неподдерживаемый тип узла: {type(node).__name__}")

if __name__ == '__main__':
    # Примеры использования для демонстрации
    print(f"10 + 20 = {safe_eval('10 + 20')}")
    print(f"5 * (10 - 2) = {safe_eval('5 * (10 - 2)')}")
    print(f"10 / 0 = {safe_eval('10 / 0')}")
    print(f"import os = {safe_eval('__import__(\"os\").system(\"ls\")')}")
