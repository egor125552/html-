import tkinter as tk
import ast
import operator as op

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        # Поле для вывода
        self.display = tk.Entry(master, width=20, font=('Arial', 16), borderwidth=2, relief="solid", justify='right')
        self.display.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        self.display.insert(0, "")

        # Кнопки
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', 'C', '=', '+'
        ]

        row = 1
        col = 0
        for button_text in buttons:
            tk.Button(master, text=button_text, width=5, height=2, font=('Arial', 14),
                      command=lambda text=button_text: self.on_button_click(text)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def safe_eval(self, expr):
        """Безопасно вычисляет математическое выражение."""
        # Поддерживаемые операторы
        operators = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv
        }

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                return operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            else:
                # Запретить все остальное
                raise TypeError(f"Неподдерживаемый тип узла: {type(node)}")

        # Разбираем выражение, затем вычисляем AST
        parsed_ast = ast.parse(expr, mode='eval')
        return _eval(parsed_ast)

    def on_button_click(self, text):
        if text == 'C':
            self.display.delete(0, tk.END)
        elif text == '=':
            try:
                expression = self.display.get()
                result = self.safe_eval(expression)
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
            except ZeroDivisionError:
                self.display.delete(0, tk.END)
                self.display.insert(0, "Деление на 0")
            except (SyntaxError, TypeError, ValueError):
                self.display.delete(0, tk.END)
                self.display.insert(0, "Ошибка")
        else:
            self.display.insert(tk.END, text)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
