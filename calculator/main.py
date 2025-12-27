import tkinter as tk
from tkinter import font
import ast

class CalculatorApp:
    """
    Класс для создания приложения-калькулятора с использованием tkinter.
    """
    ERROR_MSG = "Ошибка"

    def __init__(self, master):
        """
        Инициализирует калькулятор.
        """
        self.master = master
        master.title("Доступный калькулятор")
        master.resizable(False, False)

        # Настройки стиля для доступности
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_bg_color = "#4A4A4A"
        self.button_active_bg_color = "#6C6C6C"
        self.display_font = font.Font(family="Helvetica", size=36, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=24)

        master.configure(bg=self.bg_color)

        # Поле для ввода и отображения
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            master,
            textvariable=self.display_var,
            font=self.display_font,
            bg=self.bg_color,
            fg=self.fg_color,
            bd=0,
            justify="right",
            insertbackground=self.fg_color # Цвет курсора
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=20, sticky="nsew")

        # Создание кнопок с новым макетом
        buttons = [
            ('(', 1, 0), (')', 1, 1), ('C', 1, 2), ('/', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('*', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0, 2), ('.', 5, 2), ('=', 5, 3)
        ]

        for button_spec in buttons:
            text = button_spec[0]
            row = button_spec[1]
            col = button_spec[2]
            columnspan = button_spec[3] if len(button_spec) > 3 else 1
            self.create_button(text, row, col, columnspan)

        # Настройка сетки
        for i in range(6): # 1 ряд для дисплея + 5 рядов для кнопок
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)


    def create_button(self, text, row, col, columnspan=1):
        """
        Создает и размещает кнопку в сетке.
        """
        button = tk.Button(
            self.master,
            text=text,
            font=self.button_font,
            bg=self.button_bg_color,
            fg=self.fg_color,
            bd=0,
            activebackground=self.button_active_bg_color,
            activeforeground=self.fg_color,
            height=2,
            width=4,
            command=lambda: self.on_button_click(text)
        )
        button.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=5, sticky="nsew")
        return button

    def on_button_click(self, char):
        """
        Обрабатывает нажатия кнопок.
        """
        current_text = self.display_var.get()
        if current_text == self.ERROR_MSG:
            self.display_var.set("")
            current_text = ""

        if char == 'C':
            self.display_var.set("")
        elif char == '=':
            self.calculate()
        else:
            self.display_var.set(current_text + char)

    def calculate(self):
        """
        Вычисляет выражение в поле ввода.
        """
        expression = self.display_var.get()
        try:
            # Безопасное вычисление выражения
            result = self.safe_eval(expression)
            self.display_var.set(str(result))
        except Exception:
            self.display_var.set(self.ERROR_MSG)

    def safe_eval(self, expr):
        """
        Безопасно вычисляет математическое выражение, используя ast.
        """
        tree = ast.parse(expr, mode='eval')
        return self._eval_node(tree.body)

    def _eval_node(self, node):
        """
        Рекурсивно вычисляет узлы AST.
        """
        if isinstance(node, ast.Num): # Для старых версий Python
            return node.n
        if isinstance(node, ast.Constant): # Для Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Деление на ноль")
                return left / right
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            operand = self._eval_node(node.operand)
            return -operand

        raise TypeError(f"Неподдерживаемая операция: {type(node)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
