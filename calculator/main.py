# -*- coding: utf-8 -*-
import tkinter as tk
import ast

# Константы для цветов и шрифтов
BG_COLOR = "#212121"
FG_COLOR = "#FFFFFF"
BUTTON_BG_COLOR = "#424242"
BUTTON_FG_COLOR = "#FFFFFF"
BUTTON_ACTIVE_BG_COLOR = "#616161"
FONT = ("Helvetica", 20)
LARGE_FONT = ("Helvetica", 48, "bold")
SMALL_FONT = ("Helvetica", 16)
ERROR_MSG = "Ошибка"
ZERO_DIV_MSG = "Деление на ноль"

class CalculatorApp:
    """
    Класс для создания калькулятора с графическим интерфейсом на Tkinter.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Доступный калькулятор")
        self.root.geometry("400x600")
        self.root.configure(bg=BG_COLOR)

        self.expression = ""
        self.total_expression = ""
        self.create_widgets()
        self.update_display()
        self.root.bind("<Key>", self.on_key_press)

    def create_widgets(self):
        """Создает и размещает виджеты в окне калькулятора."""
        display_frame = tk.Frame(self.root, bg=BG_COLOR)
        display_frame.pack(expand=True, fill="both")

        buttons_frame = tk.Frame(self.root, bg=BG_COLOR)
        buttons_frame.pack(expand=True, fill="both")

        self.total_label = tk.Label(display_frame, text="", anchor="e", bg=BG_COLOR, fg=FG_COLOR, padx=24, font=SMALL_FONT)
        self.total_label.pack(expand=True, fill="both")

        self.current_label = tk.Label(display_frame, text="", anchor="e", bg=BG_COLOR, fg=FG_COLOR, padx=24, font=LARGE_FONT)
        self.current_label.pack(expand=True, fill="both")

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 1), ('.', 4, 0), ('C', 4, 2), ('+', 4, 3),
            ('=', 5, 0, 4)
        ]

        for (text, row, col, *span) in buttons:
            self.add_button(buttons_frame, text, row, col, *span)

        for i in range(1, 6):
            buttons_frame.rowconfigure(i, weight=1)
            for j in range(4):
                buttons_frame.columnconfigure(j, weight=1)

    def add_button(self, container, text, row, col, colspan=1, rowspan=1):
        btn = tk.Button(
            container, text=text, font=FONT, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
            activebackground=BUTTON_ACTIVE_BG_COLOR, activeforeground=BUTTON_FG_COLOR,
            relief="flat", borderwidth=0, command=lambda t=text: self.on_button_click(t)
        )
        btn.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, sticky="nsew", padx=1, pady=1)

    def on_button_click(self, char):
        if char == "C":
            self.expression = ""
            self.total_expression = ""
        elif char == "=":
            if self.expression:
                self.total_expression = self.expression
                self.evaluate()
        else:
            self.expression += str(char)

        self.update_display()

    def on_key_press(self, event):
        """Обработчик нажатия клавиш."""
        key = event.char
        keysym = event.keysym

        if keysym == "Return" or keysym == "KP_Enter":
            self.on_button_click("=")
        elif keysym == "Escape":
            self.on_button_click("C")
        elif keysym == "BackSpace":
            self.expression = self.expression[:-1]
            self.update_display()
        elif key in "0123456789./*-+":
            self.on_button_click(key)
        elif keysym.startswith("KP_") and keysym.replace("KP_", "").isdigit():
             self.on_button_click(keysym.replace("KP_", ""))
        elif keysym in ["KP_Add", "KP_Subtract", "KP_Multiply", "KP_Divide", "KP_Decimal"]:
            key_map = {
                "KP_Add": "+", "KP_Subtract": "-", "KP_Multiply": "*",
                "KP_Divide": "/", "KP_Decimal": "."
            }
            self.on_button_click(key_map[keysym])


    def evaluate(self):
        try:
            result = self.safe_eval(self.expression)
            self.expression = str(result)
        except (ValueError, SyntaxError):
            self.expression = ERROR_MSG
        except ZeroDivisionError:
            self.expression = ZERO_DIV_MSG

    def safe_eval(self, expr):
        tree = ast.parse(expr, mode='eval')
        if not self._check_nodes(tree.body):
            raise ValueError("Недопустимая операция")
        return eval(compile(tree, filename='<ast>', mode='eval'))

    def _check_nodes(self, node):
        allowed_nodes = {
            ast.Expression, ast.Constant, ast.Num,
            ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
            ast.UnaryOp, ast.USub, ast.UAdd
        }
        if type(node) in allowed_nodes:
            for child in ast.iter_child_nodes(node):
                if not self._check_nodes(child):
                    return False
            return True
        return False

    def update_display(self):
        self.current_label.config(text=self.expression or "0")
        self.total_label.config(text=self.total_expression)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
