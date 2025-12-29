import tkinter as tk
import ast

# Безопасное вычисление выражения
def safe_eval(expr):
    # Разрешенные узлы AST
    allowed_nodes = {
        ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub
    }

    # Проверка, что в выражении нет запрещенных узлов
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if not isinstance(node, tuple(allowed_nodes)):
            raise ValueError("Недопустимая операция")

    return eval(compile(tree, filename='<string>', mode='eval'))

class CalculatorApp:
    ERROR_MSG = "Ошибка"

    def __init__(self, master):
        self.master = master
        master.title("Доступный калькулятор")

        # Настройка высококонтрастной темы
        master.configure(bg="#2E2E2E")
        self.entry_font = ("Helvetica", 24, "bold")
        self.button_font = ("Helvetica", 18)
        self.fg_color = "#FFFFFF"
        self.bg_color = "#2E2E2E"
        self.button_bg = "#4A4A4A"
        self.button_active_bg = "#6A6A6A"

        # Поле для ввода
        self.display = tk.Entry(
            master,
            font=self.entry_font,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.fg_color,
            fg=self.fg_color,
            bg=self.bg_color,
            justify="right",
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=10, sticky="nsew")

        # Расположение кнопок
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("C", 4, 2), ("+", 4, 3),
            ("=", 5, 0, 4),
        ]

        # Создание кнопок
        for (text, row, col, *span) in buttons:
            self.create_button(text, row, col, span[0] if span else 1)

        # Настройка сетки
        for i in range(6):
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)

        # Привязка клавиши Enter для вычисления
        master.bind("<Return>", self.calculate)

    def create_button(self, text, row, col, span):
        button = tk.Button(
            self.master,
            text=text,
            font=self.button_font,
            fg=self.fg_color,
            bg=self.button_bg,
            activebackground=self.button_active_bg,
            activeforeground=self.fg_color,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.on_button_click(text),
        )
        button.grid(row=row, column=col, columnspan=span, sticky="nsew", padx=5, pady=5)
        return button

    def on_button_click(self, char):
        if char == "C":
            self.display.delete(0, tk.END)
        elif char == "=":
            self.calculate()
        else:
            self.display.insert(tk.END, char)

    def calculate(self, event=None):
        try:
            expression = self.display.get()
            result = safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, self.ERROR_MSG)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
