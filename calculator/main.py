import tkinter as tk
import ast
import operator as op

# Поддерживаемые операторы
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
}

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        # Настройка цветов
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_bg = "#505050"
        self.button_fg = "#FFFFFF"
        self.button_active_bg = "#6E6E6E"

        master.configure(bg=self.bg_color)

        # Экран для вывода
        self.display = tk.Entry(master, width=20, font=("Arial", 24), bd=10, insertwidth=2, bg="#404040", fg=self.fg_color, justify='right')
        self.display.grid(row=0, column=0, columnspan=4, pady=10, padx=10, ipady=10)

        # Создание кнопок
        buttons = [
            '(', ')', 'C', '/',
            '7', '8', '9', '*',
            '4', '5', '6', '-',
            '1', '2', '3', '+',
            '0', '.', '=', ''
        ]

        row = 1
        col = 0
        for button_text in buttons:
            if not button_text:
                continue
            if button_text == '=':
                tk.Button(master, text=button_text, padx=20, pady=20, font=("Arial", 18),
                          bg=self.button_bg, fg=self.button_fg, activebackground=self.button_active_bg,
                          command=self.calculate).grid(row=row, column=col, padx=5, pady=5)
            elif button_text == 'C':
                tk.Button(master, text=button_text, padx=20, pady=20, font=("Arial", 18),
                          bg=self.button_bg, fg=self.button_fg, activebackground=self.button_active_bg,
                          command=self.clear_display).grid(row=row, column=col, padx=5, pady=5)
            else:
                tk.Button(master, text=button_text, padx=20, pady=20, font=("Arial", 18),
                          bg=self.button_bg, fg=self.button_fg, activebackground=self.button_active_bg,
                          command=lambda t=button_text: self.on_button_click(t)).grid(row=row, column=col, padx=5, pady=5)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def on_button_click(self, char):
        self.display.insert(tk.END, char)

    def clear_display(self):
        self.display.delete(0, tk.END)

    def calculate(self):
        try:
            expression = self.display.get()
            # Безопасное вычисление выражения
            result = self._safe_eval(expression)
            self.clear_display()
            self.display.insert(0, str(result))
        except Exception as e:
            self.clear_display()
            self.display.insert(0, "Ошибка")

    def _safe_eval(self, expression):
        try:
            tree = ast.parse(expression, mode='eval').body
            return self._eval_node(tree)
        except (SyntaxError, TypeError, KeyError, ZeroDivisionError):
            raise Exception("Ошибка вычисления")

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):  # Для чисел
            return node.n
        elif isinstance(node, ast.BinOp):  # Для бинарных операций
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return operators[type(node.op)](left, right)
        else:
            raise TypeError(f"Неподдерживаемый тип узла: {type(node)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
