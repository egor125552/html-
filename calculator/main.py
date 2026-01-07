import tkinter as tk
import ast
import operator as op

# Поддерживаемые операторы
binary_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv
}
unary_operators = {
    ast.USub: op.neg
}

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")
        master.configure(bg="#2E2E2E")

        self.expression = ""
        self.equation = tk.StringVar()
        self.just_calculated = False

        # Поле для вывода выражения
        self.display = tk.Entry(master, textvariable=self.equation, font=('Arial', 24), bd=10, insertwidth=2, width=14, borderwidth=4, bg="#4A4A4A", fg="white", justify='right')
        self.display.grid(row=0, column=0, columnspan=4)

        # Кнопки калькулятора
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '.', '+'
        ]

        row_val = 1
        col_val = 0
        for button in buttons:
            action = lambda x=button: self.press(x)
            tk.Button(master, text=button, font=('Arial', 18), padx=20, pady=20, bd=8, bg="#6C6C6C", fg="white", command=action).grid(row=row_val, column=col_val)
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        # Кнопка "="
        action = lambda x='=': self.press(x)
        tk.Button(master, text='=', font=('Arial', 18), padx=20, pady=20, bd=8, bg="#6C6C6C", fg="white", command=action).grid(row=5, column=0, columnspan=4, sticky='nsew')


    def press(self, num):
        if num == '=':
            try:
                result = self.safe_eval(self.expression)
                float_result = float(result)
                self.equation.set(float_result)
                self.expression = str(float_result)
                self.just_calculated = True
            except Exception:
                self.equation.set("Ошибка")
                self.expression = ""
                self.just_calculated = False
        elif num == 'C':
            self.expression = ""
            self.equation.set("")
            self.just_calculated = False
        else:
            if self.just_calculated:
                if num in '/*-+':
                    self.just_calculated = False
                else:
                    self.expression = ""
                    self.just_calculated = False

            self.expression = self.expression + str(num)
            self.equation.set(self.expression)

    def safe_eval(self, expr):
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body)
        except (SyntaxError, TypeError, ZeroDivisionError):
            raise

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num): # Для обратной совместимости
            return node.n
        elif isinstance(node, ast.BinOp):
            if type(node.op) in binary_operators:
                left = self._eval_node(node.left)
                right = self._eval_node(node.right)
                return binary_operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) in unary_operators:
                operand = self._eval_node(node.operand)
                return unary_operators[type(node.op)](operand)
        raise TypeError(f"Неподдерживаемый узел: {type(node).__name__}")


if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
