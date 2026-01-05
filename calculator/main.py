import tkinter as tk

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        # Настройки для доступности
        self.font = ('Arial', 18)
        self.dark_bg = '#1e1e1e'
        self.light_fg = '#d4d4d4'
        self.button_bg = '#333333'
        self.button_active_bg = '#444444'
        self.result_bg = '#252526'

        master.configure(bg=self.dark_bg)
        master.resizable(False, False)

        # Поле для вывода результата
        self.display = tk.Entry(master, width=15, font=('Arial', 24), bd=0, justify='right',
                                bg=self.result_bg, fg=self.light_fg, insertbackground=self.light_fg)
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=15, ipady=10)

        # Создание кнопок
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        row = 1
        col = 0
        for button_text in buttons:
            self.create_button(button_text).grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Кнопка очистки
        self.create_button('C', self.clear_display).grid(row=row, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Настройка сетки
        for i in range(5):
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)


    def create_button(self, text, command=None):
        if command is None:
            command = lambda: self.on_button_click(text)

        return tk.Button(self.master, text=text, font=self.font,
                         bg=self.button_bg, fg=self.light_fg,
                         activebackground=self.button_active_bg, activeforeground=self.light_fg,
                         bd=0, height=2, command=command)

    def on_button_click(self, char):
        if char == '=':
            self.calculate_result()
        else:
            current_text = self.display.get()
            self.display.delete(0, tk.END)
            self.display.insert(0, current_text + char)

    def calculate_result(self):
        try:
            result = self.safe_eval(self.display.get())
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Ошибка")

    def safe_eval(self, expr):
        import ast
        import operator as op

        operators = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv
        }

        def _eval_node(node):
            if isinstance(node, (ast.Constant, ast.Num)): # ast.Num для совместимости
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                return operators[type(node.op)](left, right)
            else:
                raise TypeError(node)

        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)


    def clear_display(self):
        self.display.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
